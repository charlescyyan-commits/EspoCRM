Espo.define('custom:views/commercial-intelligence/workspace', 'view', function (Dep) {
    var GOVERNED_SOURCE_TYPES = [
        'AIJob',
        'AIRequestLog',
        'ResearchEvidence',
        'AIQualificationInsight',
        'HumanFeedback',
        'ProspectCandidate',
        'ProspectRun',
        'ExecutionLedger',
        'ReplyEvent',
        'OptimizationInsight',
        'PerformanceMetric',
        'FeedbackLearningObservation',
        'ReplySignal',
        'OpportunityCandidate',
        'RevenueInsight',
        'PipelineMetric',
    ];
    var CRM_CORE_TYPES = ['Account', 'Contact', 'Opportunity'];

    return Dep.extend({

        template: 'custom:commercial-intelligence/workspace',

        // D2: every rendered region is marked as AI/assembled and carries
        // the advisory designation. This surface issues read-only GET
        // requests only — no write request of any kind exists here.

        setup: function () {
            this.candidateId = this.options.candidateId || null;
            this.loading = true;
            this.error = false;
            this.context = null;
            this.sections = [];
            this.freshnessSummary = null;
            this.advisoryDesignation = null;
            this.wait(this.loadContext());
        },

        data: function () {
            return {
                loading: this.loading,
                error: this.error,
                hasContext: !!this.context,
                hasAnchor: !!this.candidateId,
                context: this.context,
                sections: this.sections,
                hasSections: this.sections.length > 0,
                freshnessSummary: this.freshnessSummary,
                advisoryDesignation: this.advisoryDesignation,
            };
        },

        loadContext: function () {
            if (!this.candidateId) {
                this.loading = false;
                return Promise.resolve();
            }

            var self = this;

            // The single read-only request this surface ever issues.
            return Espo.Ajax.getRequest(
                'CommercialIntelligence/workspace/' + encodeURIComponent(this.candidateId)
            ).then(function (payload) {
                self.context = payload;
                self.advisoryDesignation = payload.advisoryDesignation || null;
                self.freshnessSummary = payload.freshnessSummary || null;
                self.sections = self.buildSections(payload);
                self.loading = false;
            }).catch(function () {
                self.error = true;
                self.loading = false;
            });
        },

        buildSections: function (payload) {
            var order = [
                ['c24', 'C24 revenue evidence'],
                ['c21', 'C21 intelligence context'],
                ['c22', 'C22 execution history'],
                ['c23', 'C23 optimization context'],
                ['crmCore', 'CRM Core context'],
                ['c20', 'C20 provenance context'],
            ];

            var sections = [];
            var source = payload.sections || {};
            var self = this;

            order.forEach(function (entry) {
                var references = source[entry[0]] || [];
                if (!references.length) {
                    return;
                }
                sections.push({
                    key: entry[0],
                    title: entry[1],
                    references: references.map(function (reference) {
                        return self.presentReference(reference, payload);
                    }),
                });
            });

            return sections;
        },

        presentReference: function (reference, payload) {
            var item = Object.assign({}, reference);
            var href = this.navigationReference(reference, payload);

            item.isNavigable = !!href;
            item.navigationReference = href;

            return item;
        },

        navigationReference: function (reference, payload) {
            var entityType = reference.entityType || '';
            var entityId = reference.entityId || '';

            if (!/^[A-Za-z0-9]{8,36}$/.test(entityId)) {
                return null;
            }

            if (GOVERNED_SOURCE_TYPES.indexOf(entityType) !== -1) {
                var href = '#CommercialIntelligenceWorkspace/source/entityType='
                    + encodeURIComponent(entityType)
                    + '&entityId='
                    + encodeURIComponent(entityId);
                var anchorId = payload.anchor && payload.anchor.entityId;

                if (/^[A-Za-z0-9]{8,36}$/.test(anchorId || '')) {
                    href += '&candidateId=' + encodeURIComponent(anchorId);
                }

                return href;
            }

            if (CRM_CORE_TYPES.indexOf(entityType) !== -1) {
                return '#' + entityType + '/view/' + encodeURIComponent(entityId);
            }

            return null;
        },
    });
});
