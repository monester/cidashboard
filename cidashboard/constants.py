STATUS_SUCCESS = 1
STATUS_FAIL = 2
STATUS_SKIP = 4
STATUS_ABORTED = 8
STATUS_IN_PROGRESS = 16  # Q: Do we really need it?
STATUS_ERROR = 32

JENKINS_STATUSES = {
   'SUCCESS': STATUS_SUCCESS,
   'FAILURE': STATUS_FAIL,
   'SKIPPED': STATUS_SKIP,
   'ABORTED': STATUS_ABORTED,
   'IN_PROGRESS': STATUS_IN_PROGRESS,
   'ERROR': STATUS_ERROR,
}

TRIGGER_TIMER = 1
TRIGGER_GERRIT = 2
TRIGGER_MANUAL = 4
TRIGGER_ANY = 7
TRIGGER_TYPE_DEFAULT = 'Timer'
TRIGGER_TYPE_CHOICES = {
    TRIGGER_TIMER: 'Timer',
    TRIGGER_GERRIT: 'Gerrit trigger',
    TRIGGER_MANUAL: 'Manual',
    TRIGGER_ANY: 'Any',
}

TRIGGER_MESSAGES = {
    TRIGGER_TIMER: 'Started by timer',
    TRIGGER_GERRIT: 'Triggered by Gerrit',
    TRIGGER_MANUAL: 'Started by user',
    TRIGGER_ANY: '',
}

LDAP_USER_PERMISSIONS = (
    action + '_' + model
    for action in ('add', 'change', 'delete')
    for model in (
        'productci',
        'cisystem',
        'rulecheck',
        'rule',
        'status',
        'productcistatus',
    )
)
