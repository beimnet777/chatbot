from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to='department_pdfs/')

    def __str__(self):
        return self.name
