from django.db import models


class Note(models.Model):
    note_text = models.CharField(max_length=200)
    create_date = models.DateTimeField('date created')

    def __str__(self):
        return self.note_text
