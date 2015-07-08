from django import forms


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class SimpleFileForm(forms.Form):
    file = forms.FileField(required=False)