Espo.define('custom:controllers/commercial-intelligence-workspace', 'controllers/base', function (Dep) {
    return Dep.extend({

        // Read-only surface: no create, edit, or remove actions exist here.

        actionIndex: function () {
            this.main('custom:views/commercial-intelligence/workspace');
        },

        actionView: function (options) {
            options = options || {};
            this.main('custom:views/commercial-intelligence/workspace', {
                candidateId: options.candidateId || options.id || null,
            });
        },

        actionSource: function (options) {
            options = options || {};
            this.main('custom:views/commercial-intelligence/source-detail', {
                entityType: options.entityType || null,
                entityId: options.entityId || null,
                candidateId: options.candidateId || null,
            });
        },
    });
});
