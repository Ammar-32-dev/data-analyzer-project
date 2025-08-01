from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import DataUploadForm
from .data_analyzer import DataAnalyzer
import chardet
import csv
from .utils import send_analysis_email
import pandas as pd
import io
import logging
import zipfile
from django.urls import reverse

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

                # Store data in session for download functionality
                request.session['original_df'] = df.to_json()
                request.session['processed_df'] = analyzer.df.to_json()
                request.session['plots'] = plots
                request.session['summaries'] = summaries

                email_sent_message = None
                recipient_email = form.cleaned_data.get('recipient_email')
                if recipient_email:
                    try:
                        send_analysis_email(recipient_email, "Data Analysis Visualizations", "Please find attached the data analysis visualizations.", plots)
                        email_sent_message = f"Analysis results sent to {recipient_email}"
                    except Exception as e:
                        email_sent_message = f"Failed to send email: {e}"

                return render(request, 'analyzer_app/results.html', {
                    'plots': plots, 
                    'summaries': summaries, 
                    'email_sent_message': email_sent_message
                })

            except Exception as e:
                error_message = f"Error processing file: {e}"
                return render(request, 'analyzer_app/index.html', {'form': form, 'error_message': error_message})
    else:
        form = DataUploadForm()
    return render(request, 'analyzer_app/index.html', {'form': form})


def download_plot(request, plot_index):
    plots = request.session.get('plots', [])
    
    if 0 <= plot_index < len(plots):
        plot = plots[plot_index]
        image_data = plot['image']
        
        # Decode base64 image data
        import base64
        image_bytes = base64.b64decode(image_data)
        
        # Create HTTP response with image data
        response = HttpResponse(image_bytes, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{plot["title"].replace(" ", "_")}.png"'
        return response
    else:
        return HttpResponse("Plot not found", status=404)


def download_summary(request, summary_type):
    summaries = request.session.get('summaries', {})
    
    if summary_type in summaries:
        summary_data = summaries[summary_type]
        
        # Create a text response with summary data
        response_content = f"Data Analysis Summary ({summary_type})\n"
        response_content += "=" * 50 + "\n\n"
        
        for key, value in summary_data.items():
            response_content += f"{key.upper()}:\n"
            response_content += "-" * 20 + "\n"
            response_content += str(value) + "\n\n"
        
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="summary_{summary_type}.txt"'
        return response
    else:
        return HttpResponse("Summary not found", status=404)


def download_data(request, data_type):
    import json
    
    if data_type == 'original':
        df_json = request.session.get('original_df')
        filename = 'original_data.csv'
    elif data_type == 'processed':
        df_json = request.session.get('processed_df')
        filename = 'processed_data.csv'
    else:
        return HttpResponse("Invalid data type", status=400)
    
    if df_json:
        # Convert JSON back to DataFrame
        df = pd.read_json(df_json)
        
        # Convert DataFrame to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Create HTTP response with CSV data
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse("Data not found", status=404)


def download_all_plots(request):
    plots = request.session.get('plots', [])
    
    if not plots:
        return HttpResponse("No plots available", status=404)
    
    # Create a zip file containing all plots
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, plot in enumerate(plots):
            image_data = plot['image']
            import base64
            image_bytes = base64.b64decode(image_data)
            zip_file.writestr(f"{plot['title'].replace(' ', '_')}.png", image_bytes)
    
    # Create HTTP response with zip data
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="all_plots.zip"'
    return response
