from django.db import models

# Create your models here.


class ObjectTypes(models.Model):
    title = models.CharField(max_length=20)
    sql = models.CharField(max_length=20)
