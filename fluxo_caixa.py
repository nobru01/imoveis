# %%
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyxirr import xirr
pd.options.display.float_format = '{:,.2f}'.format


def impota_dados(path):
    ''' Essa função impora dos dados dfo csv.
    Args.:
        path => ex.: './sqs310_bloco_C_ap608/input_fluxo_caixa_SQS310C608.csv'
    '''    
    df_input=pd.read_csv(path,header=None,index_col=0)
    df_input=df_input.rename(columns={1:'valor_variavel'})
    return df_input

df_input=impota_dados('./sqs110_bloco_a_ap202/sqs110_bloco_a_ap202.csv')

valor_imovel=df_input.loc['valor_imovel','valor_variavel']
entrada_pp=df_input.loc['entrada_pp','valor_variavel']
entrada_por_valor=df_input.loc['entrada_por_valor','valor_variavel']
financiamento_0_ou_1=df_input.loc['financiamento_0_ou_1','valor_variavel']
area=df_input.loc['area','valor_variavel']
receita_aluguel_0_ou_1=df_input.loc['receita_aluguel_0_ou_1','valor_variavel']
aluguel_recebido=df_input.loc['aluguel_recebido','valor_variavel']
valor_venda=df_input.loc['valor_venda','valor_variavel']
prazo_obra=df_input.loc['prazo_obra','valor_variavel']
prazo_venda=int(prazo_obra+df_input.loc['prazo_venda_pos_obra','valor_variavel'])                # Prazo da obra em mesês + venda
comissao=df_input.loc['comissao','valor_variavel']
atualizacao_valor_imovel=df_input.loc['atualizacao_valor_imovel','valor_variavel']




# %% [markdown]
# # Custos Iniciais

# %%
itbi_parcelado_0_ou_1=df_input.loc['itbi_parcelado_0_ou_1','valor_variavel']
custo_itbi=0.03*valor_imovel
custo_escritura=df_input.loc['custo_escritura','valor_variavel']
custo_registro=df_input.loc['custo_registro','valor_variavel']


# %% [markdown]
# # Cálculo financiamento

# %%
# Cálculo do juros em função do mês
def parcela(n):
    saldo_devedor=valor_finaciado-(n-1)*amortizacao
    juros=saldo_devedor*juros_nominal/12
    return amortizacao+juros+encargos_finaciamento


# %%
if financiamento_0_ou_1==1:
    n_parcelas=int(df_input.loc['n_parcelas','valor_variavel'])                         # 35 anos
    df=pd.DataFrame(columns=['parcela','saldo_devedor'],index=range(0,n_parcelas))
    juros_nominal=df_input.loc['juros_nominal','valor_variavel']                        # a.a    
    juros_tr=df_input.loc['tr','valor_variavel']                        # a.a
    juros_nominal=juros_nominal+juros_tr
    custo_avaliacao=df_input.loc['custo_avaliacao','valor_variavel']
    juros_efetivo=((1+juros_nominal/12)**(12)-1)            # Efeito anual dos juros sobre juros mensais.  

    # he usual way to test for a NaN is to see if it's equal to itself:
    if entrada_por_valor!=entrada_por_valor:
        # Não digitou o valor da entrada
        if entrada_pp!=entrada_pp:
            print('Digite o valor da entrada ou seu percentual.')
        else:
            valor_entrada=valor_imovel*entrada_pp
    else:
        valor_entrada=entrada_por_valor
    
    valor_finaciado=valor_imovel-valor_entrada
    encargos_finaciamento=df_input.loc['encargos_finaciamento','valor_variavel']
    amortizacao=valor_finaciado/n_parcelas
    saldo_devedor=valor_finaciado

else:
    amortizacao=0
    saldo_devedor=0
    n_parcelas=0   
    juros_nominal=0
    custo_avaliacao=0
    juros_efetivo=0  
    valor_finaciado=0
    encargos_finaciamento=0
    valor_entrada=valor_imovel
    df=pd.DataFrame()

# %%
total_custos_iniciais=valor_entrada+custo_escritura+custo_registro+custo_avaliacao

# %%
for i in range(0,max(24,n_parcelas+1)):             # Se não for financiado seta o df para 24 linhas inicialmente
    if i==0:
        df.loc[i,'saldo_devedor']=valor_finaciado-i*amortizacao
        df.loc[i,'parcela']=0
    else:

        df.loc[i,'saldo_devedor']=valor_finaciado-i*amortizacao
        df.loc[i,'parcela']=parcela(i)

# %%
# ITBI
if itbi_parcelado_0_ou_1==1:
    for i in range(0,len(df)):
        if i <10:
            df.loc[i,'itbi']=custo_itbi/10
        else:
            df.loc[i,'itbi']=0
else:
    df.loc[0,'itbi']=custo_itbi
    for i in range(1,len(df)):
        df.loc[0,'itbi']=0

# %% [markdown]
# # Custos fixos


if receita_aluguel_0_ou_1==0:
    
    condominio=df_input.loc['condominio','valor_variavel']
    iptu_am=df_input.loc['iptu_aa','valor_variavel']/12
    luz=df_input.loc['luz','valor_variavel']

    total_custos_fixos=condominio+iptu_am+luz
elif receita_aluguel_0_ou_1==1:
    total_custos_fixos=-aluguel_recebido

else:
    print("Favor escolher variável receita_aluguel_0_ou_1 com valores 0 ou 1.")
    exit()

# %%
for i in range(0,len(df)):
    df.loc[i,'custos_fixos']=total_custos_fixos
    if i==0:
        df.loc[i,'custos_iniciais']=total_custos_iniciais
    else:
        df.loc[i,'custos_iniciais']=0

# %% [markdown]
# # Custos com reforma

# %%
obra=df_input.loc['obra','valor_variavel']
prazo_obra=df_input.loc['prazo_obra','valor_variavel']                # Prazo da obra em mesês

def reforma(i, n,total):
    if i==0:
        return 0
    elif i<=n:
        return total/n
    else:
        return 0

for i in range(0,len(df)):
    df.loc[i,'reforma']=reforma(i,prazo_obra,obra)

# %% [markdown]
# # Cenários de venda

def atualizacao_valor_venda(valor_venda,atualizacao_valor_imovel,prazo_venda):
    '''Atualiza o valor de venda para considerar a valorização do imóvel com o passar do tempo.'''

    valor_venda=valor_venda*(1+atualizacao_valor_imovel)**(prazo_venda/12)

    return valor_venda

def venda(i, n,total):
    if i==n:
        print(f'Comissão: {comissao*valor_venda}')
        return -total*(1-comissao)
    else:
        return 0

valor_venda=atualizacao_valor_venda(valor_venda,atualizacao_valor_imovel,prazo_venda)

for i in range(0,len(df)):
    df.loc[i,'venda']=venda(i,prazo_venda,valor_venda)
df['total']=df.sum(axis=1)
df['total']=df['total']-df['saldo_devedor']

# quitação do saldo devedor e anulação das despesas à partir:
# Da venda, da quitação do ITBI e da
for i in range(0,len(df)):
    if i>prazo_venda:
        if df.loc[i,'itbi']!=0:                                     # caso tenha parcela do ITBI ainda para pagar
            df.loc[i,'total']=df.loc[i,'itbi']
        else:
            df.loc[i,'total']=0
        
        # Quitação do saldo devedor e retirada dos custos fixos e parcelas
        df.loc[i,'saldo_devedor']=0 
        df.loc[i,'parcela']=0    
        df.loc[i,'custos_fixos']=0    

    elif i==prazo_venda:                                            
        df.loc[i,'total']=df.loc[i,'total']+df.loc[i,'saldo_devedor']
        
    

# %%
delta = relativedelta(months=1)
delta_d = timedelta(days=1)
start_date = datetime.today().date()+15*delta_d

for i in range(0, len(df)):
    if i==0:
        df.loc[i,'data']=start_date
    else:
        df.loc[i,'data']=start_date+i*delta

# Filtra apenas até a célula de venda
df=df[df['total']!=0]
print(df)

# %%
# Importa output da BcB_forcast (os dois diretórios no mesmo caminho)
df_juros_real=pd.read_csv(r'../BcB_Forcast/output/num_indice_selic_ipca_diferenca.csv', index_col=0)
df_juros_real


def busca_num_indice_selic(data):
    #converte data em string
    data=datetime.strftime(data,'%Y-%m-%d')    
    return df_juros_real.loc[data,'num_indice_selic']

def corrige_selic(total,num_selic):
    # Número índice de referência (data da venda)
    num_indice_ref=df.loc[df.index[-1],'num_selic']
    total=total*num_indice_ref/num_selic
    return total

# Tenta calcular considerendo projeções da SELIC
## Para prazos longos não vai funcionar, pq não terá projeção da SELIC
try:
        
    df['num_selic']=df.apply(lambda x: busca_num_indice_selic(x.data),axis=1)
    df['total_selic']=df.apply(lambda x: corrige_selic(x.total,x.num_selic),axis=1)
    # Indicação para calcular SELIC = 1 ou não =0
    flag_selic=1
except:
    print('Erro no cálculo utilizando as projeções da SELIC.')
    # Indicação para calcular SELIC = 1 ou não =0
    flag_selic=0


# %%
# calculo da IRR
def cal_irr(x,flag_selic):
    
    dates=list(x['data'])
    amounts=list(x['total'])
    t_aa=xirr(dates, amounts)
    t_am=(1+t_aa)**(1/12)-1
    print('TII a.a.(%): ',t_aa*100)
    print('TII a.m.(%): ',t_am*100)
    print('Lucro: ',-x['total'].sum())

    if flag_selic==1:
            
        amounts_selic=list(x['total_selic'])
        t_aa=xirr(dates, amounts_selic)
        t_am=(1+t_aa)**(1/12)-1
        print('TII a.a. acima da selic (%): ',t_aa*100)
        print('TII a.m. acima da selic (%): ',t_am*100)
        print('Lucro: ',-x['total_selic'].sum())
    
    # return (t_aa*100,t_am*100,-x['total'].sum())

# %%
cal_irr(df,flag_selic)

# %%
valor_m2_aquisicao=valor_imovel/area
print(f'm2 aquisição: {valor_m2_aquisicao}')
valor_m2_venda=valor_venda/area
print(f'm2 reforma: {obra/area}')
print(f'm2 venda: {valor_m2_venda}')


# %%
11*66+70

# %%
### projeções de inflação e crescimento econômico para evolução dos preços de venda


