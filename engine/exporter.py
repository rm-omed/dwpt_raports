import os
import comtypes.client
import traceback
import platform

def docx_to_pdf(input_path: str, output_path: str = None) -> str:
    input_path = os.path.abspath(input_path)

    if not output_path:
        output_path = input_path.replace(".docx", ".pdf")
    else:
        output_path = os.path.abspath(output_path)

    try:
        print(f"[DEBUG] Converting to PDF: {input_path} -> {output_path}")
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0

        doc = word.Documents.Open(input_path)
        doc.SaveAs(output_path, FileFormat=17)
        doc.Close(False)

        word.Quit()
    except Exception as e:
        print("[ERROR] Word crash during docx_to_pdf")
        traceback.print_exc()
        raise e

    return output_path


def print_file(path: str):
    if platform.system() == "Windows":
        os.startfile(path, "print")
    else:
        print("Printing not supported on this platform.")
