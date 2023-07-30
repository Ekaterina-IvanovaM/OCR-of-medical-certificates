import streamlit as st
from img2table.ocr import EasyOCR
from img2table.document import Image
import TableToCsv as ta
import TableExtractor1 as te
from transformers import DetrImageProcessor, DetrForObjectDetection

processor = DetrImageProcessor.from_pretrained("TahaDouaji/detr-doc-table-detection")
model = DetrForObjectDetection.from_pretrained("TahaDouaji/detr-doc-table-detection")


def table_extractor_(path, processor, model):
    table_extractor = te.TableExtractor(path, processor, model)
    perspective_corrected_image = table_extractor.execute()
    
def use_ocr(path):
    doc = Image(path)
    ocr = EasyOCR(lang=["ru"])
    doc.to_xlsx('result/table.xlsx',
            ocr=ocr,
            implicit_rows=False,
            borderless_tables=False)


def main():
    st.set_page_config(layout="wide")
    st.markdown(
        """ 
        # Приложение для распознавания справок 405 формы
        ## Загрузите справку в формате jpg
        """
    )
    
    image_file = st.file_uploader(label='Загрузите справку в формате jpg', type='jpeg')
    col1, col2 = st.columns(2)
    with col1:
        if image_file is not None:
            st.image(image=image_file)
            with open('result/original.jpg', 'wb') as file:
                file.write(image_file.getbuffer())
    table_extractor_('result/original.jpg', processor, model)
    use_ocr('result/result.jpg')
    path = 'result/table.xlsx'
    table_to_csv = ta.TableToCsv(path)
    try:
        table = table_to_csv.result()
        data = pd.read_csv('result/csv_table.csv')
        with col2:
            st.markdown(
                            """ 
                            ## Справка 405 в формате csv
                            """
                        )
            st.dataframe(data=data)
        
            with open('result/csv_table.csv', 'r') as file:
                st.download_button(label='Загрузить справку в формате csv',
                                data=file, 
                                file_name='405 справка.csv')
    except:
        st.markdown(
        """ 
        ## Загрузите изображение получше
        """
    )
    st.markdown(            """ 
                            ## Справка 405 в формате xlsx
                            """
                        )   
    data_exel = pd.read_excel('result/table.xlsx')
    st.dataframe(data=data_exel)
    with open('result/table.xlsx', "rb") as template_file:
        template_byte = template_file.read()
        st.download_button(label="Скачать исходный файл в формате xlsx",
                        data=template_byte,
                        file_name="405 справка.xlsx",
                        mime='application/octet-stream')
    

if __name__== '__main__':
    main()
