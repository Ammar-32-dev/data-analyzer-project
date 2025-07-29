from django import forms

class DataUploadForm(forms.Form):
    data_file = forms.FileField()
    file_type = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('excel', 'Excel')],
        initial='csv',
        widget=forms.RadioSelect,
        label="File Type"
    )
    recipient_email = forms.EmailField(
        required=False,
        label="Recipient Email (Optional)",
        help_text="If you want the results emailed to you, enter your email address here."
    )