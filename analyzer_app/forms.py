from django import forms

class DataUploadForm(forms.Form):
    data_file = forms.FileField()
    file_type = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('excel', 'Excel')],
        initial='csv',
        widget=forms.RadioSelect,
        label="File Type"
    )