from mongoengine import Document, fields, EmbeddedDocument
from dj_cqrs.mixins import ReplicaMixin


class Curso(EmbeddedDocument):
    id = fields.ObjectIdField(primary_key=True, editable=False)
    grado = fields.StringField(max_length=100)
    numero = fields.IntField()
    anio = fields.IntField()

    def __str__(self):
        return f"{self.grado} - {self.numero}"


class Institucion(ReplicaMixin, Document):
    CQRS_ID = 'instituciones-model'

    nombreInstitucion = fields.StringField(max_length=100)
    cursos = fields.ListField(fields.EmbeddedDocumentField(Curso))

    def __str__(self):
        return self.nombreInstitucion



