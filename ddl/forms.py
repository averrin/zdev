from django import forms


from registration.models import MysqlCreds
attrs_dict = {'class': 'required', 'required': 'required'}


class MySQLCreds(forms.ModelForm):
    class Meta:
        model = MysqlCreds
        exclude = ('user',)
        widgets = {
            'db_login': forms.TextInput(attrs=attrs_dict),
            'db_password': forms.PasswordInput(attrs=attrs_dict, render_value=True)
        }

    # def clean_db_login(self):
    #     data = self.cleaned_data['db_login']
    #     if data != "averrin":
    #         raise forms.ValidationError("You are not averrin!")

    #     return data
