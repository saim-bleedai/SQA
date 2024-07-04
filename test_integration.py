from dotenv import load_dotenv
load_dotenv("E:/Bleed Ai/Tim finance OCR/owl/.env") #give path to env on your machine
import unittest
from unittest.mock import patch, MagicMock
from app.services.chart.service import ChartAnalyzer
from app.services.chart.service import ChartAnalyzer, db, ChartDBService, embedding_model
import base64
from PIL import Image
import io
import os





class TestChartAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ChartAnalyzer()
        self.output_folder = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/ouput_folder"
        self.test_pdf_path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/2022-01-27_AAPL_Earnings_Release.pdf"
        self.document_name = "test_document"
        self.results = ["Data chart 1", "Data chart 2", "No data charts found"]

    
    def test_chart_exists_true(self):  # testing the chart exists function with the actual response from the LLM. Expected output is that LLM returns true
        
       
        path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/Chart.jpeg" #giving an actual path. Replace path with the path of the Chart.jpeg image on your machine
        result = self.analyzer._ChartAnalyzer__chart_exists(path)
        #print(result)
        self.assertTrue(result)

    
    def test_chart_exists_false(self):  # testing the chart exists function with mocking the LLM response when llm returns no
        
        
        path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/add1.jpg" #giving an image path that doesnot contain a chart. Replace with a path when running test on your local machine
        result = self.analyzer._ChartAnalyzer__chart_exists(path)
        # print(result)
        self.assertFalse(result)

    def test_chart_exists_invalid_path(self): #giving an invalid file path to the function to test the result. will remove the function once discussed
        # Invalid file path
        invalid_path = "invalid/path/to/nonexistent/file.jpg"
        
        # Execute the function and check for ValueError
        # This checks that the function itself throws a ValueError when faced with an invalid path
        with self.assertRaises(ValueError) as context:
            self.analyzer._ChartAnalyzer__chart_exists(invalid_path)

        # Optionally check that the exception message is correct
        self.assertIn("Image string must be one of: b64 encoded image string (data:image/...), valid image url, or existing local image file.", str(context.exception))


    
    def test_analyze_chart(self):  # giving the llm an image that doesnot contain a chart to check the actual output of the LLM
        
        test_image_path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/add1.jpg"

        # Base64 encoded string simulating a JPEG image
        with Image.open(test_image_path) as img:
            # Ensure the image is in an acceptable format (e.g., JPEG)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=img.format)
            img_bytes = img_bytes.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        # img_b64 = get_base64_image(test_image_path)
        # print("Base64 String:", img_b64)

        # Call the method under test
        response = self.analyzer._ChartAnalyzer__analyze_chart(img_b64)
        #print(response)

        # Assert the expected outcomes
        
        self.assertIn("No data charts found", response)
    
    def test_analyze_image_with_chart(self): # giving the llm an image that doesnot contain a chart to check the actual output of the LLM
        test_image_path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/Chart.jpeg"

        # Base64 encoded string simulating a JPEG image
        with Image.open(test_image_path) as img:
            # Ensure the image is in an acceptable format (e.g., JPEG)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=img.format)
            img_bytes = img_bytes.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # print("Base64 String:", img_b64)

        # Call the method under test
        response = self.analyzer._ChartAnalyzer__analyze_chart(img_b64)
        #print(response)

        # Assert the expected outcomes
        
        self.assertNotIn("No data charts found", response)

    def test_analyze(self): #giving the analyze function an earnings release document to test if it analyzes 
        _, analysis_results  = self.analyzer.analyze(self.test_pdf_path)

         # Print the results
        
        # print("Analysis Results:")
        # for result in analysis_results:
        #     print(result)
            #self.assertIn("No data charts found", result) or self.assertIn("False Positive, No data charts found", result)
        
       
        
        self.assertEqual(len(analysis_results), 3)  # Ensure some results are returned
        expected_messages = ["No data charts found", "False Positive, No data charts found"]
        for result in analysis_results:
            self.assertIn(result, expected_messages)


        
    def test_analyze_deck(self):#giving the analyze function a deck document
       file_path ="E:/Bleed Ai/Tim finance OCR/owl/service/tests/2023-06-20_FDX_Shareholder_Deck.pdf"
       _, analysis_results = self.analyzer.analyze(file_path) 
       self.assertEqual(len(analysis_results), 17)#ensuring the function has iterated over each page
       page_six_result = analysis_results[5]
    #     undesired_messages = ["False Positive, No data charts found", "No data charts found"]
    #     # Assert that none of the undesired messages are in the result for page 6
    #     for message in undesired_messages:
    #         with self.subTest(message=message):
    #             self.assertNotIn(message, page_six_result) #needs fix should not return this message

         # Print the results
       #print("Output Folder:", output_folder)
       print("Analysis Results:")
       for result in analysis_results:
            print(result)

   
    # def test_save_results(self):
    #     document_name = "somename"
    #     test_image_path = "E:/Bleed Ai/Tim finance OCR/owl/Chart.jpeg"

    #     # Base64 encoded string simulating a JPEG image
    #     with Image.open(test_image_path) as img:
    #         # Ensure the image is in an acceptable format (e.g., JPEG)
    #         img_bytes = io.BytesIO()
    #         img.save(img_bytes, format=img.format)
    #         img_bytes = img_bytes.getvalue()
    #     img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    #     response = self.analyzer._ChartAnalyzer__analyze_chart(img_b64)
    #     result =self.analyzer.save_results_db(document_name, response)
    #     print(result)


       
           

if __name__ == "__main__":
    unittest.main()
