from django.utils.translation import gettext_lazy as _
from jet.dashboard.modules import DashboardModule
from audit.models import YourOrganization, HintList, Hint
from audit.admin import admin_change_link, admin_add_link, admin_changelist_link

class Stat(DashboardModule):
    title = _('Registry Status')
    template = 'dashboard_modules/stat.html'

    class Media:
        js = ('js/chart.bundle.min.js', 'js/utils.js')

    def init_with_context(self, context):
        hints = HintList()
        if not YourOrganization.objects.count():
            link = admin_add_link('yourorganization', _("Primeira vez aqui? Clique para adicionar uma/sua empresa/organização no sistema"))
            hints.append(Hint(obj="", hint_type='suggestion',
                        text=link))

        else:
            for i, org in enumerate(YourOrganization.objects.all()):
                if not i:
                    link = admin_changelist_link(org,
                                          _("Clique aqui para ver todas as empresas/organizações do sistema e gerar um relatório em PDF para cada uma"))
                    hints.append(Hint(obj="", hint_type='suggestion',
                                      text=link))
                hints.extend(org.get_hints())
            hints.set_admin_change_link(admin_change_link)
            suggestions = hints.list['suggestion']
            if not suggestions:
                hints.append(Hint(obj="", hint_type='suggestion',
                                 text=_("O LGPD é um processo contínuo. Certifique-se de que todos os seus processos de negócios e atividades de tratamento/processamento de dados que gerenciam dados pessoais sejam atualizados neste registro.")))
        self.children = hints