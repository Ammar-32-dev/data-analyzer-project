from django.shortcuts import render, redirect
from .forms import CSVUploadForm
from .data_analyzer import DataAnalyzer
from .utils import send_analysis_email
import pandas as pd
import io

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            # Read the CSV file into a pandas DataFrame
            try:
                # Try reading with utf-8 first
                csv_data = csv_file.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(csv_data))
            except UnicodeDecodeError:
                try:
                    # If utf-8 fails, try ISO-8859-1
                    csv_data = csv_file.read().decode('ISO-8859-1')
                    df = pd.read_csv(io.StringIO(csv_data))
                except Exception as e:
                    return render(request, 'analyzer_app/index.html', {'form': form, 'error_message': f'Error reading CSV: {e}'})
            except Exception as e:
                return render(request, 'analyzer_app/index.html', {'form': form, 'error_message': f'Error reading CSV: {e}'})

            # Save the DataFrame to a temporary CSV file for DataAnalyzer
            # In a real application, you might want to handle this more robustly
            # For simplicity, we'll write it to a temp file.
            temp_csv_path = 'temp_upload.csv'
            df.to_csv(temp_csv_path, index=False)

            analyzer = DataAnalyzer(temp_csv_path)
            plots = analyzer.run_analysis()

            # Clean up the temporary file
            import os
            os.remove(temp_csv_path)

            email_sent_message = None
            recipient_email = form.cleaned_data.get('recipient_email')
            if recipient_email:
                try:
                    send_analysis_email(recipient_email, "Data Analysis Visualizations", "Please find attached the data analysis visualizations.", plots)
                    email_sent_message = f"Analysis results sent to {recipient_email}"
                except Exception as e:
                    email_sent_message = f"Failed to send email: {e}"

            return render(request, 'analyzer_app/results.html', {'plots': plots, 'email_sent_message': email_sent_message})
    else:
        form = CSVUploadForm()
    return render(request, 'analyzer_app/index.html', {'form': form})