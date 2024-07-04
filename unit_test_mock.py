from dotenv import load_dotenv
load_dotenv("E:/Bleed Ai/Tim finance OCR/owl/.env")
import unittest
from unittest.mock import patch, MagicMock, call
from app.services.chart.service import ChartAnalyzer
import base64
from PIL import Image
import io
import os
from itertools import cycle




class TestChartAnalyzer(unittest.TestCase):
    def setUp(self):
        with patch('app.services.chart.service.LLMService.get_llm') as mock:
            # Create a mock for the `invoke` method directly
            self.mock_invoke = MagicMock()
            # Initialize the mock here but will set return values in individual tests
            #mock.return_value.llm.invoke = self.mock_invoke
            mock.return_value.llm = MagicMock(invoke=self.mock_invoke)

            # Initialize the analyzer with the mock in place
            self.analyzer = ChartAnalyzer()
            #self.output_folder = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/ouput_folder"
            #self.test_pdf_path = "E:/Bleed Ai/Tim finance OCR/owl/service/tests/2022-01-27_AAPL_Earnings_Release.pdf"


    def test_chart_exists_mock_llm_response_no(self): # testing the chart exists function with mocking the LLM response when llm returns yes
        # Set the mock to return 'no'
        self.mock_invoke.return_value.content = "no"
        path = "test/path/to/your/file"  # Path does not matter as LLM response is being mocked
        result = self.analyzer._ChartAnalyzer__chart_exists(path)
        #print (result)
        self.assertFalse(result, "Expected False, got: {}".format(result))


    def test_chart_exists_api_key_expired(self):
        # Mock the LLM service to simulate an API authentication failure
        error_message = "API key invalid or expired"
        self.mock_invoke.side_effect = Exception(error_message)

        path = "valid/path/to/image.jpg"
        
        # Execute the function and check that it raises the correct exception
        with self.assertRaises(Exception) as context:
            self.analyzer._ChartAnalyzer__chart_exists(path)

        # Check that the exception message contains the expected text
        self.assertIn(error_message, str(context.exception))

   


    def test_analyze_chart_no_charts_found(self): #testing the chart analyze chart function with mocking the LLM response when llm does not find any charts in the image.
        # Set the mock to simulate a response indicating no charts are present
        self.mock_invoke.return_value.content = "No data charts found"
        
        
        test_img = "mock image converted to text"

        # Call the method under test
        response = self.analyzer._ChartAnalyzer__analyze_chart(test_img)
        #print("Response from analyze chart:", response)

        # Assert the expected outcomes
        self.assertIn("No data charts found", response)   

    def test_analyze_chart_charts_found(self): #testing the chart analyze chart function with mocking the LLM response when llm finds charts in the image.
    # Set the mock to simulate a response indicating charts are present
     chart_details = "Detailed explanation of the charts in the image."
     self.mock_invoke.return_value.content = chart_details
     test_img = "mock image converted to text"
    
    

    # Call the method under test
     response = self.analyzer._ChartAnalyzer__analyze_chart(test_img)
     #print(response)

    # Assert the expected outcomes
     self.assertIn(chart_details, response)


    @patch('os.makedirs')
    @patch('os.listdir')
    @patch('PIL.Image.open', new_callable=MagicMock)
    def test_analyze_document(self, mock_image_open, mock_listdir, mock_makedirs):
        mock_listdir.return_value = ['1.jpg', '2.jpg', '3.jpg']
        mock_image = MagicMock(spec=Image.Image)
        mock_image_open.return_value = mock_image

        with patch.object(self.analyzer, '_ChartAnalyzer__convert_to_jpg') as mock_convert, \
             patch.object(self.analyzer, '_ChartAnalyzer__chart_exists') as mock_exists, \
             patch.object(self.analyzer, '_ChartAnalyzer__analyze_chart') as mock_analyze:

            mock_exists.side_effect = cycle([True, False, True])
            mock_analyze.side_effect = [
                "Detailed analysis of chart on page 1",
                "No data charts found on page 2",
                "Detailed analysis of chart on page 3"
            ]

            test_pdf_path = "mock_document.pdf"
            _, analysis_results = self.analyzer.analyze(test_pdf_path)
            #print("expected result",analysis_results)

            expected_results = [
                "Detailed analysis of chart on page 1",
                "No data charts found on page 2",
                "Detailed analysis of chart on page 3"
            ]
            self.assertEqual(len(analysis_results), 3) #expecting the document has 3 pages
            self.assertEqual(analysis_results, expected_results)



    @patch('os.makedirs')
    @patch('os.listdir')
    @patch('PIL.Image.open', new_callable=MagicMock)
    def test_analyze_no_charts_document(self, mock_image_open, mock_listdir, mock_makedirs):#testing the chart analyze chart function with mocking the LLM response when llm finds no charts in the pages.
       mock_listdir.return_value = ['1.jpg', '2.jpg', '3.jpg']
       mock_image_open.return_value = MagicMock(spec=Image.Image)

       with patch.object(self.analyzer, '_ChartAnalyzer__convert_to_jpg') as mock_convert, \
         patch.object(self.analyzer, '_ChartAnalyzer__chart_exists') as mock_exists, \
         patch.object(self.analyzer, '_ChartAnalyzer__analyze_chart') as mock_analyze:

        mock_exists.side_effect = cycle([False, False, False])  # No charts on any pages
        mock_analyze.side_effect = [
            "No data charts found on page ",
            "No data charts found on page ",
            "No data charts found on page "
        ]

        test_pdf_path = "no_charts_document.pdf"
        _, analysis_results = self.analyzer.analyze(test_pdf_path)

        expected_results = [
            "No data charts found",
            "No data charts found",
            "No data charts found"
        ]
        self.assertEqual(len(analysis_results), 3)
        self.assertEqual(analysis_results, expected_results)


    @patch('os.makedirs')
    @patch('os.listdir')
    @patch('PIL.Image.open', new_callable=MagicMock)
    def test_analyze_all_charts_document(self, mock_image_open, mock_listdir, mock_makedirs): #testing the chart analyze chart function with mocking the LLM response when llm finds charts in all the pages.
      mock_listdir.return_value = ['1.jpg', '2.jpg', '3.jpg']
      mock_image_open.return_value = MagicMock(spec=Image.Image)

      with patch.object(self.analyzer, '_ChartAnalyzer__convert_to_jpg') as mock_convert, \
         patch.object(self.analyzer, '_ChartAnalyzer__chart_exists') as mock_exists, \
         patch.object(self.analyzer, '_ChartAnalyzer__analyze_chart') as mock_analyze:

        mock_exists.side_effect = cycle([True, True, True])  # All pages have charts
        mock_analyze.side_effect = [
            "Detailed analysis of chart on page 1",
            "Detailed analysis of chart on page 2",
            "Detailed analysis of chart on page 3"
        ]

        test_pdf_path = "all_charts_document.pdf"
        _, analysis_results = self.analyzer.analyze(test_pdf_path)

        expected_results = [
            "Detailed analysis of chart on page 1",
            "Detailed analysis of chart on page 2",
            "Detailed analysis of chart on page 3"
        ]
        self.assertEqual(len(analysis_results), 3)
        self.assertEqual(analysis_results, expected_results)
    


    @patch('os.makedirs')
    @patch('os.listdir', return_value=[])  # No files to list, simulating an empty directory
    @patch('PIL.Image.open', new_callable=MagicMock)
    def test_analyze_empty_document(self, mock_image_open, mock_listdir, mock_makedirs): #sending an empty list to the function to test the response 
    # Mocking '__convert_to_jpg' to do nothing since there are no images
       with patch.object(self.analyzer, '_ChartAnalyzer__convert_to_jpg') as mock_convert:
          mock_convert.return_value = None  # Ensure this does not affect the flow
          test_pdf_path = "empty_document.pdf"
          _, analysis_results = self.analyzer.analyze(test_pdf_path)
          #print(analysis_results)
          self.assertEqual(len(analysis_results), 0, "Expected no analysis results for an empty document")    

        
    @patch('os.makedirs')
    @patch('os.listdir')
    @patch('PIL.Image.open', side_effect=IOError("Failed to open image"))  # Simulate image opening failure
    def test_analyze_corrupted_document(self, mock_image_open, mock_listdir, mock_makedirs): #testing the behavior of the function if one of the images is corrupted
     mock_listdir.return_value = ['1.jpg', '2.jpg', '3.jpg']

     with patch.object(self.analyzer, '_ChartAnalyzer__convert_to_jpg'), \
         patch.object(self.analyzer, '_ChartAnalyzer__chart_exists') as mock_exists, \
         patch.object(self.analyzer, '_ChartAnalyzer__analyze_chart') as mock_analyze:

        mock_exists.return_value = False
        mock_analyze.return_value = "Analysis failed due to corrupted page"

        test_pdf_path = "corrupted_document.pdf"
        with self.assertRaises(IOError):
            _, analysis_results = self.analyzer.analyze(test_pdf_path)
            #print(analysis_results)



    
    @patch('app.services.chart.service.ChartDBService.exists')
    @patch('app.services.chart.service.ChartDBService.create_chart_analysis_table')
    @patch('app.services.chart.service.db.session')
    def test_save_results_db(self, mock_db_session, mock_create_table, mock_exists): # Tests that the save_results_db function correctly interacts with the database to save analysis results.It verifies that the database service is called correctly for each result and that the correct database operations(addition and commit) are performed based on whether the analysis result already exists in the database.
        
        # Setup the mocks
        mock_exists.return_value = False
        mock_create_table.return_value = MagicMock()
        
        # Prepare the test data
        document_name = "test_document"
        results = ["chart analysis result"]
        
        # Call the function under test
        self.analyzer.save_results_db(document_name, results)

         # Assert that print was called correctly
        #mock_print.assert_called_with("Saving page number 1 to DB")
        
        # Assert that the database check was made
        mock_exists.assert_called_once_with(document_name, 1)
        
        # Assert that the table creation was triggered
        mock_create_table.assert_called_once()
        
        # Assert that the session add and commit were called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


    @patch('app.services.chart.service.ChartDBService.exists')
    @patch('app.services.chart.service.ChartDBService.create_chart_analysis_table')
    @patch('app.services.chart.service.db.session')
    def test_save_results_db_multiple_records(self, mock_db_session, mock_create_table, mock_exists):
        """
        Tests that the save_results_db function correctly handles multiple records, creating new entries only for those
        that do not already exist in the database. Verifies that database operations are performed appropriately
        based on the existence check for each result.
        """
        # Configure the exists check to simulate varied database presence
        mock_exists.side_effect = [False, True, False]
        
        # Prepare the test data
        document_name = "test_document"
        results = ["result 1", "result 2", "result 3"]
        
        # Call the function under test
        self.analyzer.save_results_db(document_name, results)
        
        # Assert correct handling of each result based on its pre-existence in the database
        expected_calls = [call(document_name, i + 1) for i in range(len(results))]
        mock_exists.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_create_table.call_count, 2)  # Only 2 new records should be created because the second already exists
        
        # Assert that the database transactions were handled correctly
        self.assertEqual(mock_db_session.add.call_count, 2)  # Add should be called twice, for the new records
        mock_db_session.commit.assert_called_once()

    @patch('app.services.chart.service.ChartDBService.exists')
    @patch('app.services.chart.service.ChartDBService.create_chart_analysis_table')
    @patch('app.services.chart.service.db.session')
    def test_save_results_db_empty_results(self, mock_db_session, mock_create_table, mock_exists):
        """
        Tests that the save_results_db function handles an empty results list correctly, ensuring that no database operations
        are performed when there are no results to process.
        """
        # Prepare the test data
        document_name = "test_document"
        results = []
        
        # Call the function under test
        self.analyzer.save_results_db(document_name, results)
        
        # Assert that no database operations were called
        mock_exists.assert_not_called()
        mock_create_table.assert_not_called()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @patch('app.services.chart.service.ChartDBService.exists')
    @patch('app.services.chart.service.ChartDBService.create_chart_analysis_table')
    @patch('app.services.chart.service.db.session')
    def test_save_results_db_commit_integrity(self, mock_db_session, mock_create_table, mock_exists):
        """
        Tests that the save_results_db function properly handles database transactions, particularly verifying
        that it does not commit changes if an error occurs during the creation of new records. This ensures the
        atomicity of database operations.
        """
        # Setup the mocks to simulate database behavior
        mock_exists.side_effect = [False, False]  # No existing records
        # Simulate an error on the second insert to test transaction integrity
        mock_create_table.side_effect = [MagicMock(), Exception("Failure on second insert")]
        
        # Prepare the test data
        document_name = "test_document"
        results = ["result 1", "result 2"]
        
        # Execute the function and expect an exception
        with self.assertRaises(Exception):
            self.analyzer.save_results_db(document_name, results)
        
        # Verify that a commit was not called due to the exception
        mock_db_session.commit.assert_not_called()
        # Ensure that rollback is called to revert partial changes
        #mock_db_session.rollback.assert_called_once()

if __name__ == '__main__':
    unittest.main()        

