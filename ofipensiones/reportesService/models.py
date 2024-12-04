from mongoengine import Document, fields, EmbeddedDocument

class Curso(EmbeddedDocument):
    id = fields.ObjectIdField(primary_key=True, editable=False)
    grado = fields.StringField(max_length=100)
    numero = fields.IntField()
    anio = fields.IntField()

    def __str__(self):
        return f"{self.grado} - {self.numero}"

class Institucion(Document):

    nombreInstitucion = fields.StringField(max_length=100)
    cursos = fields.ListField(fields.EmbeddedDocumentField(Curso))

    def __str__(self):
        return self.nombreInstitucion

class Estudiante(Document):
    nombreEstudiante =  fields.StringField(max_length=100)
    codigoEstudiante = fields.StringField(max_length=50)

    # Relaciones con otras BD
    institucionEstudianteId = fields.ObjectIdField(editable=False)
    nombreInstitucion = fields.StringField(max_length=100)
    cursoEstudianteId = fields.ObjectIdField()

    def __str__(self):
        return self.nombreEstudiante

class DetalleCobroCurso(EmbeddedDocument):
    id = fields.ObjectIdField(primary_key=True, editable=False)
    mes = fields.StringField(max_length=20)
    valor = fields.DecimalField(max_digits=10, decimal_places=2)
    fechaCausacion = fields.DateTimeField()
    fechaLimite = fields.DateTimeField()
    frecuencia = fields.StringField(max_length=50)

    def __str__(self):
        return f"Cobro de {self.mes} - Valor {self.valor}"

class CronogramaBase(Document):
    institucionId = fields.ObjectIdField(editable=False)
    nombreInstitucion = fields.StringField(max_length=100)
    cursoId = fields.ObjectIdField(editable=False)
    grado = fields.StringField(max_length=50)

    codigo = fields.StringField(max_length=50)
    nombre = fields.StringField(max_length=100)
    detalle_cobro = fields.ListField(fields.EmbeddedDocumentField(DetalleCobroCurso))

    def __str__(self):
        return self.nombre

class ReciboCobro(Document):
    fecha = fields.DateTimeField()
    nmonto = fields.DecimalField(max_digits=10, decimal_places=2)
    detalle = fields.StringField(max_length=100)
    estudiante = fields.ReferenceField(Estudiante)
    detalles_cobro = fields.ListField(fields.EmbeddedDocumentField(DetalleCobroCurso))

    def calcular_monto_total(self):
        return sum(detalle.valor for detalle in self.detalles_cobro.all())

    def __str__(self):
        return f"Recibo {self.id} - {self.nmonto}"

class ReciboPago(Document):
    recibo_cobro = fields.ReferenceField(ReciboCobro)
    fecha = fields.DateTimeField()
    nmonto = fields.DecimalField(max_digits=10, decimal_places=2)
    detalle = fields.StringField(max_length=100)

    def __str__(self):
        return f"Recibo Pago {self.id} - {self.nmonto}"