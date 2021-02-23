# Copyright (c) 2020 Igino Corona, Pluribus One SRL;
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see https://www.gnu.org/licenses/

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.template.defaultfilters import truncatewords
from django.utils.html import format_html
import hashlib
import PyPDF2
from collections import OrderedDict

HINT_TYPES = OrderedDict([
                            ('suggestion', _("Sugestões")),
                            ('issue', _("Problemas")),
                            ('warning', _("Avisos")),
                        ])

class Hint:

    def __init__(self, obj, text, hint_type):
        self.text = text
        self.obj = obj
        self.hint_type = hint_type
        try:
            self.obj_class = self.obj.__class__._meta.verbose_name.title()
        except:
            self.obj_class = ''
        assert(hint_type in HINT_TYPES)

    def __str__(self):
        return format_html("{} {} {}", self.text, self.obj_class, getattr(self.obj, 'admin_change_link', str(self.obj)))


class HintList:

    def __init__(self):
        self.list = OrderedDict((hint, []) for hint in HINT_TYPES.keys())

    def append(self, obj):
        assert(isinstance(obj, Hint))
        self.list[obj.hint_type].append(obj)

    def extend(self, hint_list):
        assert (isinstance(hint_list, HintList))
        for key, objs in hint_list.list.items():
            self.list[key].extend(objs)

    def get_items(self):
        return [(key, HINT_TYPES[key], hint_list) for key, hint_list in self.list.items()]

    def set_admin_change_link(self, admin_change_link):
        for hint_list in self.list.values():
            for hint in hint_list:
                try:
                    hint.obj.admin_change_link = admin_change_link(hint.obj, str(hint.obj))
                except:
                    pass

    @property
    def is_empty(self):
        for l in self.list.values():
            if len(l) > 0:
                return False
        return True


class Base(models.Model):
    last_update = models.DateTimeField(auto_now=True, verbose_name=_("Última atualização"))

    def get_hints(self):
        return HintList()

    class Meta:
        abstract = True


class NameDesc(Base):
    name = models.CharField(unique=True,
                            max_length=100,
                            verbose_name=_("Nome"))
    description = models.TextField(verbose_name=_("Descrição"), blank=True)

    def short_description(self):
        return truncatewords(self.description, 50)
    short_description.short_description = _("Descrição")

    def get_hints(self):
        hints = HintList()
        if not self.description:
            hints.append(Hint(obj=self, text=_("Descrição ausente em"), hint_type='warning'))
        return hints

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Organization(NameDesc):
    email = models.EmailField(verbose_name=_("E-mail"))
    address = models.CharField(max_length=50, verbose_name=_("Endereço"))
    country = models.CharField(max_length=200, verbose_name=_("País"))
    telephone = models.CharField(max_length=50, verbose_name=_("Telefone"))
    statute = models.CharField(max_length=200, verbose_name=_("Estatuto"))
    third_country = models.BooleanField(verbose_name=_("Transferência Internacioanl"), help_text=_("Marque este campo se a organização residir em um país fora do território Nacional"))
    international = models.BooleanField(verbose_name=_("Internacional"), help_text=_("Marque este campo se a organização e seus órgãos subordinados são regidos pelo direito internacional público"))

    class Meta:
        abstract = True

def media_file_name(instance, filename):
    return 'documents/{}.pdf'.format(instance.name)

class PDFDocument(NameDesc):
    document = models.FileField(verbose_name=_("Upload de arquivo/documento"), upload_to=media_file_name)
    md5sum = models.CharField(blank=True, verbose_name=_("MD5Sum"), max_length=36)

    def clean(self): # PDF file validation
        try:
            PyPDF2.PdfFileReader(self.document)
        except Exception as e:
            raise ValidationError(_("Somente arquivos PDF são aceitos"))

    def save(self, *args, **kwargs):
        if not self.pk:  # file is new
            md5 = hashlib.md5()
            for chunk in self.document.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        super(PDFDocument, self).save(*args, **kwargs)

class List(NameDesc):
    classification = models.CharField(blank=True, max_length=100, verbose_name=_("Classification"),
                                      help_text=_("Insira uma classificação geral para esta entrada (caso exista)"))
    article = models.PositiveIntegerField(null=True, blank=True,
                                          verbose_name=_("LGPD Artigo"),
                                          help_text=_("Referente ao Artigo da  LGPD  (caso exista)"))
    url = models.URLField(blank=True,
                          verbose_name=_("URL de referência"),
                          help_text=_("URL de referência (caso exista)")
                          )

    def __str__(self):
        if self.classification:
            return "{} - {}".format(self.classification, self.name)
        else:
            return super(List, self).__str__()

    class Meta:
        abstract = True



class ProcessingLegal(List):
    class Meta:
        verbose_name = _("Base Legal para Tratamento")
        verbose_name_plural = _("Base Legal para Tratamento")


class ProcessingPurpose(List):
    class Meta:
        verbose_name = _("Objetivo do Tratamento")
        verbose_name_plural = _("Objetivo do Tratamento")


class ProcessingType(List):
    class Meta:
        verbose_name = _("Tipo de Tratamento")
        verbose_name_plural = _("Tipo de Tratamento")


class DataCategory(List):
    special = models.BooleanField(verbose_name=_("Categoria Especial"),
                                  help_text=_("Marque este campo se a categoria de dados for especial. "
                                  "O Tratamento desta categoria de dados normalmente é proibido."))

    class Meta:
        verbose_name = _("Categoria de Dados Funcionais")
        verbose_name_plural = _("Categoria de Dados Funcionais")


class ProcessingActivityClassificationDocument(PDFDocument):
    class Meta:
        verbose_name = _("Documento de Classificação de Atividades de Tratamento")
        verbose_name_plural = _("Documento de Classificação de Atividades de Tratamento")


class ProcessingActivityClassificationLevel(List):
    document = models.ForeignKey(ProcessingActivityClassificationDocument, null=True, on_delete=models.DO_NOTHING,
                                 verbose_name=_("Documento de Classificação de Atividades de Tratamento"))

    class Meta:
        verbose_name = _("Nivel de Classificação da atividade de Tratamento")
        verbose_name_plural = _("Nivel de Classificação da atividade de Tratamento")


class RecipientCategory(List):
    class Meta:
        verbose_name = _("Categoria de Destinatário")
        verbose_name_plural = _("Categoria de Destinatário")


class NatureOfTransferToThirdCountry(List):
    class Meta:
        verbose_name = _("Natureza da transferência para um pais terceiro / organizacao internacional")
        verbose_name_plural = _("Natureza da transferência para um pais terceiro / organizacao internacional")


class DataSubjectCategory(List):
    vulnerable = models.BooleanField(verbose_name=_("Categoria Vulnerável"),
                                     help_text=_("Indica se os titulares dos dados sao considerados uma categoria Vulnerável. "
                                         "Marque este sinalizador se os titulares dos dados envolvidos estiverem em uma situação em que haja falta de "
                                         "paridade na relação entre o titular dos dados e o controlador, como filhos, funcionarios, pacientes, etc."
                                         "Desmarque este sinalizador se nenhuma das categorias mencionadas acima estiver envolvida."))

    class Meta:
        verbose_name = _("Categoria de Assunto de Dados")
        verbose_name_plural = _("Categoria de Assunto de Dados")


class ThirdParty(Organization):
    category =  models.ForeignKey(RecipientCategory, on_delete=models.DO_NOTHING,
                                  verbose_name=_("Categoria"),
                                  help_text=_("No contexto do Tratamento da base de consentimento, para cumprir o artigo 7"
                                  "do LGPD, os controladores precisarão fornecer uma lista completa de destinatários ou categorias de destinatarios, incluindo processadores."))
    third_country_transfer = models.ForeignKey(NatureOfTransferToThirdCountry, blank=True, null=True, on_delete=models.DO_NOTHING,
                                               verbose_name=_("Natureza da transferencia para um pais terceiro / organizacao internacional"),
                                               help_text=_("Especifique por que os dados sao transferidos para este pais terceiro / organizacao internacional"))
    appropriate_safeguards = models.TextField(verbose_name=_("Protecao de dados apropriada"), blank=True,
                                              help_text=_("Em caso de transferencia de dados para um terceiro pais / organizacao internacional "
                                              "organizacao e transferencia com base no Artigo 33 da LGPD, liste os documentos que "
                                              "esclarecer as salvaguardas apropriadas e onde esses documentos são armazenados."))

    def get_hints(self):
        hints = super().get_hints()
        if self.third_country_transfer:
            hints.extend(self.third_country_transfer.get_hints())
            if not self.appropriate_safeguards:
                hints.append(Hint(obj=self, text=_("Nenhuma salvaguarda apropriada foi especificada para transferências de dados de países terceiros / internacionais"), hint_type='issue'))
        return hints

    def clean(self):
        # TODO: add other validation, e.g., EU country/international
        if self.third_country_transfer and (not (self.third_country or self.international)):
            raise ValidationError(_("Esta Empresa nao esta marcada como pais terceiro ou internacional. Se voce deseja definir a natureza da transferencia para um pais terceiro / organizacao internacional, primeiro marque um destes campos."))

    class Meta:
        verbose_name = _("Empresa Terceirizada / Transferencia Internacional")
        verbose_name_plural = _("Empresa Terceirizada / Transferencia Internacional")

class AuditUser(Base):
    user = models.OneToOneField(User, verbose_name=_("Registered User"), on_delete=models.CASCADE)

    def __str__(self):
        if self.user.first_name:
            return "{} {}".format(self.user.first_name, self.user.last_name)
        return self.user.username

    class Meta:
        abstract = True

class DataProtectionOfficer(AuditUser):
    address = models.CharField(max_length=50, verbose_name=_("Endereço"))
    telephone = models.CharField(max_length=50, verbose_name=_("Telefone"))
    staff = models.BooleanField(verbose_name=_("Membro da equipe"),
                                help_text=_('O DPO faz parte da equipe da empresa do controlador?'))

    def get_hints(self):
        hints = super().get_hints()
        if self.staff:
            hints.append(Hint(obj=self, text=_("O DPO faz parte da equipe da empresa controladora. Você deve ser capaz de demonstrar que o DPO ser uma pessoa independente."), hint_type='warning'))
        return hints

    class Meta:
        verbose_name = _("Data Protection Officer (DPO)")
        verbose_name_plural = _("Data Protection Officers (DPOs)")


class DPIA(PDFDocument):
    class Meta:
        verbose_name = _("Relatório de Impacto a Protecao de Dados. (DPIA / RIPD)")
        verbose_name_plural = _("Relatório de Impacto a Protecao de Dados. (DPIAs / RIPDs)")


class DataSubjectRights(PDFDocument):
    class Meta:
        verbose_name = _("Documento de direitos do titular dos dados")
        verbose_name_plural = _("Documento de direitos do titular dos dados")


class ProcessorContract(PDFDocument):
    processor = models.ForeignKey(ThirdParty, on_delete=models.DO_NOTHING,
                                     verbose_name=_("Processador"),
                                     help_text=_("Empresa terceirizada com a qual o Contrato foi assinado."))

    def get_hints(self):
        hints = super().get_hints()
        hints.extend(self.processor.get_hints())
        return hints

    class Meta:
        verbose_name = _("Contrato do Processador")
        verbose_name_plural = _("Contratos do Processador")


RISK_CHOICES = (
                (0, _("Desconhecido")),
                (1, _("Baixo")),
                (2, _("Medio")),
                (3, _("Alto")),
                )

class CommonRiskHint:

    def get_hints(self):
        hints = super().get_hints()
        if self.risk == 0:
            hints.append(Hint(obj=self, text=_("Risco desconhecido para os dados pessoais para"), hint_type='issue'))
        if not self.data_set.count():
            hints.append(Hint(obj=self, text=_("Sem auditoria de dados para"), hint_type='error'))
        if not self.risk_mitigation:
            hints.append(Hint(obj=self, text=_("Nenhuma descricao de medidas de mitigacao de risco para"), hint_type='warning'))
        return hints

class DataManagementPolicy(NameDesc, CommonRiskHint):
    processor_contracts = models.ManyToManyField(ProcessorContract,
                                    verbose_name=_("Contratos do processador de dados"),
                                    help_text=_(
                                        "Se os dados forem REALMENTE transferidos para OUTRAS organizações (por exemplo, processadores de dados), "
                                        "faca upload do contrato que regula esta transferência de dados e informacoes relevantes sobre cada empresa terceirizada.."),
                                    blank=True)
    retention = models.IntegerField(null=True, blank=True, verbose_name=_("Período de retenção para os dados processados, em dias"))
    risk_mitigation = models.TextField(blank=True, verbose_name=_("Medidas de mitigação de risco"),
                                        help_text=_("Informações sobre as medidas de mitigação de risco relacionadas ao Tratamento de dados, contra violações de dados."))
    risk = models.PositiveSmallIntegerField(default=0, verbose_name=_("Residual Risk"), choices=RISK_CHOICES,
                                            help_text=_("Indique o risco residual para os direitos e liberdades fundamentais dos titulares dos dados, "
                                            "dadas as medidas de mitigação que foram postas em prática."))
    subject_rights = models.ForeignKey(DataSubjectRights, null=True, blank=True, on_delete=models.DO_NOTHING,
                            verbose_name=_("Direitos do Titular dos Dados"),
                            help_text=_("Consulte os documentos que determinam os procedimentos destinados a proteger os direitos dos titulares dos dados. "
                                        "O documento também deve indicar quais medidas especiais foram tomadas para fazer cumprir / apoiar " 
                                        "o exercício dos direitos dos titulares dos dados."))
    subject_notification = models.TextField(blank=True, verbose_name=_("Notificação do Titular dos Dados"),
                                      help_text=_("Indique como os titulares dos dados são notificados de que seus dados foram registrados."))
    comments = models.TextField(blank=True, verbose_name=_("Comentários"),
                                help_text=_("Por favor, coloque comentários sobre a política de gerenciamento de dados."))

    def get_hints(self):
        hints = super().get_hints()
        if self.risk >= 2:
            hints.append(Hint(obj=self, text=_("Risco Médio/alto de gerenciamento de dados residuais  para"), hint_type='issue'))
        if self.retention is None:
            hints.append(Hint(obj=self,
                              text=_("Nenhum valor de retenção especificado para"),
                              hint_type='issue'))
        if self.subject_rights:
            hints.extend(self.subject_rights.get_hints())
        else:
            hints.append(Hint(obj=self,
                              text=_("Falta descrição dos procedimentos adotados para salvaguardar os direitos dos titulares dos dados em"),
                              hint_type='warning'))
        if not self.subject_notification:
            hints.append(Hint(obj=self,
                              text=_("Falta descrição dos procedimentos de notificação aos titulares dos dados para"),
                              hint_type='warning'))

        for contract in self.processor_contracts.all():
            hints.extend(contract.get_hints())

        return hints

    class Meta:
        verbose_name = _("Política de Gestão de Dados")
        verbose_name_plural = _("Política de Gestão de Dados")


class DataBreachDetection(NameDesc, CommonRiskHint):
    risk_mitigation = models.TextField(blank=True, verbose_name=_("Medidas de mitigação de risco"),
                                        help_text=_("Informações sobre as medidas de mitigação de risco relacionadas à detecção de violações de dados"))
    risk = models.PositiveSmallIntegerField(default=0, verbose_name=_("Risco residual"), choices=RISK_CHOICES,
                                            help_text=_("Indique o risco residual de perder uma violação de dados devido à falta de medidas / tecnologia de detecção"))
    comments = models.TextField(blank=True, verbose_name=_("Comentários"),
                                help_text=_("Por favor, coloque comentários sobre a política de gerenciamento de dados."))

    def get_hints(self):
        hints = super().get_hints()
        if self.risk >= 2:
            hints.append(Hint(obj=self, text=_("Risco residual Médio/Alto de violação de dados perdidos para"), hint_type='issue'))
        return hints

    class Meta:
        verbose_name = _("Detecção de violação de dados")
        verbose_name_plural = _("Detecção de violação de dados")


class DataBreachResponse(NameDesc, CommonRiskHint):
    risk_mitigation = models.TextField(blank=True, verbose_name=_("Medidas de mitigação de risco"),
                                        help_text=_("Informações sobre as medidas de mitigação de risco para a resposta a violações de dados. "
                                                    "Para este fim, um plano de resposta a incidentes adequado deve ser colocado em prática, incluindo o"
                                                    "notificação obrigatória de violações de dados à autoridade supervisora ​​e todas as partes envolvidas."))
    risk = models.PositiveSmallIntegerField(default=0, verbose_name=_("Risco Residual"), choices=RISK_CHOICES,
                                            help_text=_("Indique o risco residual de não responder adequadamente a uma violação de dados devido à falta de medidas / tecnologia de detecção."))
    comments = models.TextField(blank=True, verbose_name=_("Comentários"),
                                help_text=_("Por favor, coloque comentários sobre a política de gerenciamento de dados."))


    def get_hints(self):
        hints = super().get_hints()
        if self.risk >= 2:
            hints.append(Hint(obj=self, text=_("Risco residual Médio/Alto para resposta à violação de dados em"), hint_type='issue'))
        return hints

    class Meta:
        verbose_name = _("Plano de Resposta a Incidentes")
        verbose_name_plural = _("Plano de Resposta a Incidentes")


class Data(NameDesc):
    category = models.ForeignKey(DataCategory, on_delete=models.DO_NOTHING,
                                 verbose_name=_("Categoria de Dados"))
    subject_category = models.ManyToManyField(DataSubjectCategory,
                                              verbose_name=_("Categoria de Assunto de Dados"))
    source = models.TextField(blank=True, verbose_name=_("Fonte original dos dados"),
                              help_text=_("Indique a fonte dos dados, se não os próprios titulares dos dados."))
    comments = models.TextField(verbose_name=_("Comentários"),
                                help_text=_("Por favor, coloque quaisquer comentários para a auditoria de dados."),
                                blank=True)
    risk = models.PositiveSmallIntegerField(default=0, verbose_name=_("Risco inerente"), choices=RISK_CHOICES,
                                       help_text=_("Indique o risco inerente aos direitos e liberdades fundamentais dos titulares dos dados associados à auditoria de dados."))
    management = models.ForeignKey(DataManagementPolicy, null=True, blank=True, on_delete=models.DO_NOTHING,
                                   verbose_name=_("Política de Gestão de Dados"))
    breach_detection = models.ForeignKey(DataBreachDetection, null=True, blank=True,
                                         verbose_name=_("Detecção de violação de dados"),
                                   on_delete=models.DO_NOTHING,)
    breach_response = models.ForeignKey(DataBreachResponse, null=True, blank=True,
                                        verbose_name=_("Plano de Resposta a Incidentes"),
                                   on_delete=models.DO_NOTHING,)
    dpia = models.ForeignKey(DPIA, null=True, blank=True, on_delete=models.DO_NOTHING,
                             verbose_name=_("Relatório de Impacto à Proteção de Dados"),
                             help_text=_("Se a atividade de Tratamento provavelmente envolve um alto risco para o fundamental "
                                         "direitos e liberdades dos titulares dos dados, um DPIA deve ser preenchido (LGPD Artigo 5, XVII)."))

    def get_processing_activities(self):
        return ", ".join([a.name for a in self.processingactivity_set.all()])
    get_processing_activities.short_description = _("Atividades de Tratamento")

    def get_hints(self):
        hints = super().get_hints()
        if not self.processingactivity_set.count():
            hints.append(Hint(obj=self, text=_("Nenhuma atividade de Tratamento associada a"), hint_type='error'))
        if not self.management:
            hints.append(Hint(obj=self, text=_("Nenhuma política de gerenciamento de dados especificada para"), hint_type='issue'))
        else:
            hints.extend(self.management.get_hints())

        if self.subject_category.count():
            for cat in self.subject_category.all():
                hints.extend(cat.get_hints())
        else:
            hints.append(Hint(obj=self, text=_("Nenhuma categoria de assunto especificada para"), hint_type='warning'))

        if self.risk >= 2: # MID/HIGH INHERENT RISK LEVEL
            if not self.breach_detection:
                hints.append(Hint(obj=self, text=_("Risco inerente Médio/Alto, mas nenhuma tecnologia de detecção de violação de dados especificada para"), hint_type='issue'))
            if not self.breach_response:
                hints.append(Hint(obj=self, text=_("Risco inerente Médio/Alto, mas nenhum plano de resposta à violação de dados especificado para"), hint_type='issue'))
            if self.risk >= 3 and (not self.dpia): # INHERENTLY HIGH RISK LEVEL
                hints.append(Hint(obj=self, text=_("Risco inerente Médio/Alto, mas nenhuma avaliação de impacto de proteção de dados especificada para"), hint_type='issue'))
        elif self.risk == 0:
            hints.append(Hint(obj=self, text=_("Nível de risco inerente desconhecido para"), hint_type='issue'))
        if self.breach_detection:
            hints.extend(self.breach_detection.get_hints())
        if self.breach_response:
            hints.extend(self.breach_response.get_hints())
        if self.dpia:
            hints.extend(self.dpia.get_hints())
        return hints

    class Meta:
        verbose_name = _("Auditoria de Dados")
        verbose_name_plural = _("Auditoria de Dados")

class ProcessingActivity(NameDesc):
    data_audit = models.ManyToManyField(Data, blank=True, verbose_name=_("Auditoria de Dados"),
                                        help_text=_("Especifique os dados tratados por esta atividade (saída de um processo de auditoria de dados)."))
    purpose = models.ForeignKey(ProcessingPurpose, on_delete=models.DO_NOTHING,
                                verbose_name=_("Propósito"))
    proc_type = models.ForeignKey(ProcessingType, on_delete=models.DO_NOTHING,
                                  verbose_name=_("Tipo de Tratamento"),)
    start_date = models.DateField(null=True, blank=True,
                                  verbose_name=_("Data de início"),)
    end_date = models.DateField(null=True, blank=True,
                                verbose_name=_("Data final"),
                                help_text=_("Data de término do Tratamento, se aplicável. Ao preencher esta data, você declara que o Tratamento cessa a partir dessa data."))
    legal = models.ForeignKey(ProcessingLegal, on_delete=models.DO_NOTHING,
                              verbose_name=_("Base Legal para Tratamento"),
                              help_text=_("Qual é a base legal para o Tratamento? É obrigatório!"))
    technology = models.TextField(blank=True, verbose_name=_("Tecnologia"), help_text=_("Como a atividade é realizada. Descrição das tecnologias, aplicativos e software empregados na atividade de Tratamento."), null=True)
    alternate_activity = models.ForeignKey('self', null=True, blank=True, on_delete=models.DO_NOTHING,
                                           verbose_name=_("Atividade Alternativa"),
                                           help_text=_("Quando apropriado, faça referência à atividade de Tratamento que substitui a atividade encerrada. Isso cria um histórico no registro. "
                                            "Isso pode ser útil quando a base jurídica de uma atividade de Tratamento muda, por exemplo, como resultado de uma alteração estatutária."))
    comments = models.TextField(blank=True, verbose_name=_("Comentários"),
                                help_text=_("Por favor, coloque qualquer comentário na atividade de Tratamento."))

    classification = models.ForeignKey(ProcessingActivityClassificationLevel,  on_delete=models.DO_NOTHING,
                                       verbose_name=_("Nível de Classfíciação"),
                                       help_text=_("Indique o nível de classificação da "
                                                  "atividade de Tratamento de acordo com a empresa"
                                                  "sistema de classificação (escolha o mais alto caso vários sejam "
                                                  "envolvidos)."),
                                       null=True,
                                       blank=True)

    def get_hints(self):
        hints = super().get_hints()
        if not self.get_business_process():
            hints.append(Hint(obj=self, text=_("Nenhum processo de negócios associado a"), hint_type='error'))
        if not self.start_date:
            hints.append(Hint(obj=self, text=_("Data de início ausente para"), hint_type='warning'))
        if not self.technology:
            hints.append(Hint(obj=self, text=_("Falta descrição de tecnologia para"), hint_type='warning'))
        if self.data_audit.count():
            for data in self.data_audit.all():
                hints.extend(data.get_hints())
        else:
            hints.append(Hint(obj=self, text=_("Especifique pelo menos uma auditoria de dados para"), hint_type='suggestion'))
        return hints

    def get_business_process(self):
        try:
            return self.businessprocess_set.all()[0]
        except:
            return None
    get_business_process.short_description = _('Business Process')

    def clean(self):
        try:
            if self.outsourcing.processor == self.get_business_process().get_organization():
                raise ValidationError(
                    _("A terceirização prefigura a atribuição da atividade de Tratamento a outra organização"))
        except ValidationError:
            raise
        except:
            pass

    class Meta:
        verbose_name = _("Atividade de Tratamento")
        verbose_name_plural = _("Atividades de Tratamentos")

class BusinessOwner(AuditUser):

    def get_business(self):
        return ", ".join([b.name for b in self.businessprocess_set.all()])

    def get_hints(self):
        hints = super().get_hints()
        if not self.self.businessprocess_set.count():
            hints.append(Hint(obj=self, text=_("Nenhum processo de negócios associado a"), hint_type='error'))
        return hints

    class Meta:
        verbose_name = _("Business Owner")
        verbose_name_plural = _("Business Owners")

class BusinessProcess(NameDesc):
    owner = models.ForeignKey(BusinessOwner, null=True, blank=True, on_delete=models.DO_NOTHING,
                              verbose_name=_("Process Owner"),
                              help_text=_("Indique quem é responsável e gerencia este processo de negócios."))
    activities = models.ManyToManyField(ProcessingActivity, blank=True,
                                        verbose_name=_("Atividades de Tratamento"),
                                        help_text=_("Você deve inserir todas as atividades de Tratamento que podem manipular dados pessoais como parte do processo de negócios (por exemplo, Coleta de Curriculum Vitae"))

    def get_organization(self):
        try:
            return self.yourorganization_set.all()[0]
        except:
            return None
    get_organization.short_description = _('Organization')

    def clean(self):
        """We could avoid such check using ForeignKey on each activity instead of a ManyToMany in this obj.
        However, to exploit the admin interface it is much more intuitive to use a ManyToMany in this obj and perform this additional check."""
        if self.pk is None:
            return
        for activity in self.activities.all():
            other_business = activity.businessprocess_set.all().exclude(pk=self.pk).all()
            if other_business.count():
                raise ValidationError(_("A atividade {} já está atribuída a outro processo empresarial: {}").format(activity, other_business[0]))

    def get_hints(self):
        hints = super().get_hints()
        if not self.get_organization():
            hints.append(Hint(obj=self, text=_("Nenhuma empresa associada a"), hint_type='error'))
        if not self.owner:
            hints.append(Hint(obj=self, text=_("Sem dono para"), hint_type='warning'))
        if self.activities.count():
            for activity in self.activities.all():
                hints.extend(activity.get_hints())
        else:
            hints.append(Hint(obj=self, text=_("Especifique pelo menos uma atividade de Tratamento para"), hint_type='suggestion'))
        return hints

    class Meta:
        verbose_name = _("Processo de negócio")
        verbose_name_plural = _("Processos de negócio")


class YourOrganization(Organization):
    officer = models.ForeignKey(DataProtectionOfficer, null=True, blank=True, on_delete=models.DO_NOTHING,
                                verbose_name=_("Data Protection Officer (DPO)"),
                                help_text=_("Por favor, insira o Data Protection Officer (caso exista). Um Data Protection Officers (DPO) pode ser obrigatório para "
                                "autoridades públicas, ou se determinados tipos de atividades de Tratamento são realizados pela organização. O DPO deve ser independente, um especialista em proteção de dados, de forma adequada "
                                "com recursos e reportar ao mais alto nível de gestão e administração."))
    business = models.ManyToManyField(BusinessProcess, blank=True,
                                      verbose_name=_("Processo de negócio"),
                                      help_text=_("Você deve inserir cada processo de negócios na Organização que pode lidar com dados pessoais (por exemplo, Recursos Humanos)"))
    public_authority = models.BooleanField(verbose_name=_("Autoridade pública"),
                                           help_text=_(
                                               "Marque este campo se a organização for uma autoridade pública (exceto para tribunais que atuam em sua capacidade judicial)"))
    monitoring = models.BooleanField(verbose_name=_("Monitoramento em larga escala"),
                                     help_text=_(
                                         "Marque este campo se as atividades principais da organização exigem monitoramento em larga escala, regular e sistemático de indivíduos (por exemplo, rastreamento de comportamento online)"))
    special_category = models.BooleanField(verbose_name=_("Dados Especiais"),
                                     help_text=_(
                                         "Marque este campo se as atividades principais da organização consistirem no Tratamento em grande escala de dados de categorias especiais ou dados relacionados a condenações criminais e crimes"))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hints = None

    def get_business_processes(self):
        return self.business.count()
    get_business_processes.short_description = _("Processos de Negócios")

    def clean(self):
        """We could avoid such check using ForeignKey on each business instead of a ManyToMany in this obj.
        However, to exploit the admin interface it is much more intuitive to use a ManyToMany in this obj and perform this additional check."""
        if self.pk is None:
            return
        for process in self.business.all():
            other_orgs = process.yourorganization_set.all().exclude(pk=self.pk).all()
            if other_orgs.count():
                raise ValidationError(_("Processo de negócios {} já está atribuído a outra organização: {}").format(process, other_orgs[0]))


    def get_hints(self):
        hints = super().get_hints()
        if (not self.officer) and (self.public_authority or self.monitoring or self.special_category):
            if self.public_authority:
                text = _("Autoridades públicas ")
            elif self.monitoring:
                text = _("Quando o monitoramento sistemático e em grande escala de indivíduos é realizado como atividade principal, as Organizações ")
            elif self.special_category:
                text = _("Quando o Tratamento em grande escala de dados especiais sobre indivíduos é realizado como atividade principal, Organizações ")
            hints.append(Hint(obj=self, text=_("{} deve nomear um Data Protection Officer").format(text), hint_type='issue'))
        if self.business.count():
            for process in self.business.all():
                hints.extend(process.get_hints())
        else:
            hints.append(Hint(obj=self, text=_("Insira pelo menos um processo de negócio em"), hint_type='suggestion'))
        return hints


    class Meta:
        verbose_name = _("Empresa / Organizações")
        verbose_name_plural = _("Suas Empresas  / Organizações")


