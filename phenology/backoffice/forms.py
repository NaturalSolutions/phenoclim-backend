from django import forms
from backend import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext


class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).\
                exclude(username=username).count():
            raise forms.ValidationError(ugettext('Already exists'))
        return email

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email',)


class SnowingForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y'),
                           input_formats=('%d/%m/%Y',))

    class Meta:
        model = models.Snowing
        fields = ('height', 'observer', 'remark', 'area', 'date')
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
        }


class ResetPasswordForm(forms.Form):
    email = forms.CharField(label='Email', max_length=100)

    def clean_email(self):
        email = self.cleaned_data['email']
        found = User.objects.filter(email=email).first()
        if not found:
            raise forms.ValidationError(_("User with this email doesnt exist"))
        return email


class AccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # magic
        in_creation = True
        if (not kwargs.get('instance')):
            observer = models.Observer()
            observer.user = User()
            self.user = observer.user
        else:
            if kwargs.get('instance').id:
                in_creation = False
            kwargs["instance"].id
            self.user = kwargs['instance'].user
        user_kwargs = kwargs.copy()
        user_kwargs['instance'] = self.user
        key_order = []
        if in_creation:
            self.uf = CreateUserForm(*args, **user_kwargs)
            key_order += ['username']
            self.uf.fields['email'].required = True
        else:
            self.uf = UserForm(*args, **user_kwargs)

        # magic end

        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields.update(self.uf.fields)
        self.initial.update(self.uf.initial)
        self.fields.keyOrder = key_order +\
            ['organism', 'email',
             'fonction', 'nationality',
             'codepostal',
             'category',
             'accept_policy', 'accept_email', 'accept_newsletter']

    def is_valid(self):
        # save both forms
        is_valid = super(AccountForm, self).is_valid()
        if(not self.uf.is_valid()):
            self.errors.update(self.uf.errors)
            is_valid = False
        return is_valid

    def save(self, *args, **kwargs):
        # save both forms
        instance = self.uf.save(*args, **kwargs)
        self.instance.user = instance
        return super(AccountForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Observer
        exclude = ('user', 'is_crea', 'is_active', 'areas', 'date_inscription')
        # widgets = {
        #    'adresse': forms.Textarea(attrs={'rows': 2}),
        # }


class AreaAdminForm(forms.ModelForm):
    observers = forms.fields.MultipleChoiceField(
        choices=[(a.id, unicode(a)) for a in models.Observer.objects.all()])

    class Meta:
        model = models.Area

    def __init__(self, *args, **kwargs):
        super(AreaAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            # if this is not a new object, we load related books
            self.initial['observers'] = self.instance.observer_set.\
                values_list('pk', flat=True)

    def save(self, *args, **kwargs):
        instance = super(AreaAdminForm, self).save(*args, **kwargs)
        if instance.pk:
            for observer in instance.observer_set.all():
                if observer not in self.cleaned_data['observers']:
                    # we remove books which have been unselected
                    instance.observer_set.remove(observer)
            for observer in self.cleaned_data['observers']:
                if observer not in instance.observer_set.all():
                    # we add newly selected books
                    instance.observer_set.add(observer)
        return instance


class AreaForm(forms.ModelForm):
    class Meta:
        model = models.Area
        exclude = ('species', 'polygone', 'codezone')
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
        }


class SurveyForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y'),
                           input_formats=('%d/%m/%Y',))

    class Meta:
        exclude = ('is_dead', 'status', 'comment')
        model = models.Survey
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
            'individual': forms.HiddenInput(),
            'stage': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        self.base_fields['stage'].queryset = instance.\
            individual.\
            species.\
            stage_set.filter(is_active=True).order_by("order")
        self.base_fields['stage'].label = _("Change stage")
        super(SurveyForm, self).__init__(*args, **kwargs)

    def clean_date(self):
        date = self.cleaned_data['date']
        surveys = models.Survey.objects.\
            filter(date__year=date.year,
                   individual=self.instance.individual,
                   stage=self.instance.stage)
        surveys_id = [s.id for s in surveys]
        if(self.instance.id not in surveys_id and surveys.count() > 0):
            raise forms.ValidationError(ugettext('There is already a survey '
                                                 'with same stage, '
                                                 'same individual '
                                                 'in %(year)s') % {"year": date.year})
        return date

    def save(self, commit=True):
        if(self.cleaned_data["answer"] in ("today", "before")):
            self.cleaned_data["answer"] = "isObserved"
        instance = super(SurveyForm, self).save(commit=False)
        instance.save()
        return instance


class CreateIndividualForm(forms.ModelForm):
    class Meta:
        exclude = ('is_dead',)
        model = models.Individual
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
            'area': forms.HiddenInput()
        }

    def clean_name(self):
        data = self.cleaned_data['name']
        free = self.instance.area.individual_set.\
            exclude(id=self.instance.id).filter(name=data).count() == 0
        if not free:
            raise forms.ValidationError(
                _("This name is already found in your area"))
        return data


class IndividualForm(CreateIndividualForm):
    class Meta:
        exclude = ('area',)
        model = models.Individual
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
        }


class ObserverForm(forms.ModelForm):
    class Meta:
        model = models.Observer

    def __init__(self, *args, **kwargs):
        super(ObserverForm, self).__init__(*args, **kwargs)
