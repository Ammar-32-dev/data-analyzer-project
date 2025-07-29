from django.shortcuts import render, redirect
from .forms import DataUploadForm
from .data_analyzer import DataAnalyzer
import chardet
import csv
from .utils import send_analysis_email
import pandas as pd
import io
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_file(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['data_file']
            file_type = form.cleaned_data['file_type']
            df = None
            error_message = None

            try:
                if file_type == 'csv':
                    # Read a sample to detect encoding and delimiter
                    raw_data = uploaded_file.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] if result['encoding'] else 'utf-8'
                    
                    # Try to detect delimiter
                    try:
                        sample = raw_data.decode(encoding).splitlines(True)[:5]
                        dialect = csv.Sniffer().sniff(''.join(sample))
                        delimiter = dialect.delimiter
                    except csv.Error:
                        delimiter = ',' # Default to comma if sniffing fails

                    df = pd.read_csv(io.StringIO(raw_data.decode(encoding)), sep=delimiter)
                elif file_type == 'excel':
                    df = pd.read_excel(uploaded_file)
                
                analyzer = DataAnalyzer(df=df)
                plots, summaries = analyzer.run_analysis()

                email_sent_message = None
                recipient_email = form.cleaned_data.get('recipient_email')
                if recipient_email:
                    try:
                        send_analysis_email(recipient_email, "Data Analysis Visualizations", "Please find attached the data analysis visualizations.", plots)
                        email_sent_message = f"Analysis results sent to {recipient_email}"
                    except Exception as e:
                        email_sent_message = f"Failed to send email: {e}"

                return render(request, 'analyzer_app/results.html', {'plots': plots, 'summaries': summaries, 'email_sent_message': email_sent_message})

            except Exception as e:
                error_message = f"Error processing file: {e}"
                return render(request, 'analyzer_app/index.html', {'form': form, 'error_message': error_message})
    else:
        form = DataUploadForm()
    return render(request, 'analyzer_app/index.html', {'form': form})