import os
from PyPDF2 import PdfFileMerger

path = r'C:\Users\bruno.bfn\Desktop\imoveis\sqs310_bloco_C_ap_207\Certidões\TST'
pdfs = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.pdf')]
merger = PdfFileMerger()

for pdf in pdfs:
    merger.append(pdf)

merger.write(os.path.join(path, 'TST.pdf'))
merger.close()