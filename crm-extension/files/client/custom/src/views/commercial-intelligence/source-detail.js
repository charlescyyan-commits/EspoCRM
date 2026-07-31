Espo.define('custom:views/commercial-intelligence/source-detail', 'view', function (Dep) {
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

    return Dep.extend({

        template: 'custom:commercial-intelligence/source-detail',

        setup: function () {
            this.entityType = this.options.entityType || '';
            this.entityId = this.options.entityId || '';
            this.candidateId = this.options.candidateId || '';
            this.loading = true;
            this.error = false;
            this.source = null;
            this.backHref = this.buildBackHref();
            this.wait(this.loadSource());
        },

        data: function () {
            return {
                loading: this.loading,
                error: this.error,
                hasSource: !!this.source,
                source: this.source,
                fields: this.source ? this.source.fields || [] : [],
                hasFields: !!(this.source && this.source.fields && this.source.fields.length),
                backHref: this.backHref,
            };
        },

        loadSource: function () {
            if (!this.isValidRequest()) {
                this.error = true;
                this.loading = false;
                return Promise.resolve();
            }

            var self = this;

            return Espo.Ajax.getRequest(
                'CommercialIntelligence/source/'
                + encodeURIComponent(this.entityType)
                + '/'
                + encodeURIComponent(this.entityId)
            ).then(function (payload) {
                self.source = payload;
                self.loading = false;
            }).catch(function () {
                self.error = true;
                self.loading = false;
            });
        },

        isValidRequest: function () {
            return GOVERNED_SOURCE_TYPES.indexOf(this.entityType) !== -1
                && /^[A-Za-z0-9]{8,36}$/.test(this.entityId);
        },

        buildBackHref: function () {
            if (/^[A-Za-z0-9]{8,36}$/.test(this.candidateId)) {
                return '#CommercialIntelligenceWorkspace/view/'
                    + encodeURIComponent(this.candidateId);
            }

            return '#CommercialIntelligenceWorkspace';
        },
    });
});
