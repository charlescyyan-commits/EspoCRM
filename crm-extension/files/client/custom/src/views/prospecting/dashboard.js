Espo.define('custom:views/prospecting/dashboard', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/dashboard',

        data: function () {
            return {
                loading: this.loading,
                labels: this.labels || {},
                sections: this.sections || [],
                pipeline: this.pipeline || [],
                hasSections: this.hasSections,
                hasPipeline: this.hasPipeline,
                today: this.today,
            };
        },

        setup: function () {
            this.loading = true;
            this.labels = this.buildLabels();
            this.sectionConfigs = this.buildSectionConfigs();
            this.pipelineConfigs = this.buildPipelineConfigs();
            this.sections = this.materializeSections();
            this.pipeline = this.materializePipeline();
            this.hasSections = this.sections.length > 0;
            this.hasPipeline = this.pipeline.length > 0;
            this.today = this.buildTodayLabel();
            this.wait(this.loadDashboardData());
        },

        buildLabels: function () {
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'ProspectingDashboard');
            }.bind(this);

            return {
                title: translate('operations'),
                subtitle: translate('workspaceDescription'),
                loading: translate('loading'),
                noData: translate('noData'),
                emptyState: translate('workspaceEmpty'),
                overview: translate('overview'),
                researchStatus: translate('researchStatus'),
                outreachStatus: translate('outreachStatus'),
                commercialHandoff: translate('commercialHandoff'),
                pipelineSummary: translate('pipelineSummary'),
                pendingSend: translate('pendingSend'),
                failedSend: translate('failedSend'),
                repliedPendingTriage: translate('repliedPendingTriage'),
                pendingApprovals: translate('pendingApprovals'),
                researchQueue: translate('researchQueue'),
                followUpDue: translate('followUpDue'),
                researchRework: translate('researchRework'),
                missingEvidence: translate('missingEvidence'),
                pendingOutreach: translate('pendingOutreach'),
                sentAwaitingReply: translate('sentAwaitingReply'),
                proposalReviewRequired: translate('proposalReviewRequired'),
                quoteCenterHandoff: translate('quoteCenterHandoff'),
                quoteCenterDescription: translate('quoteCenterDescription'),
                pipelineProspectPool: translate('pipelineProspectPool'),
                pipelineResearchInProgress: translate('pipelineResearchInProgress'),
                pipelineResearched: translate('pipelineResearched'),
                pipelineOutreached: translate('pipelineOutreached'),
                pipelineProposalReview: translate('pipelineProposalReview'),
            };
        },

        buildTodayLabel: function () {
            return new Date().toISOString().slice(0, 10);
        },

        buildSectionConfigs: function () {
            return [
                {
                    key: 'overview',
                    title: this.labels.overview,
                    cards: [
                        this.buildCountCard('pendingSend', 'SendExecution', 'SendExecution', 'c18ReadyToSend', '#SendExecution/list/primary=c18ReadyToSend'),
                        this.buildCountCard('failedSend', 'SendExecution', 'SendExecution', 'c18FailedSend', '#SendExecution/list/primary=c18FailedSend'),
                        this.buildCountCard('repliedPendingTriage', 'ReplyEvent', 'ReplyEvent', 'c19OpenReplies', '#ReplyEvent/list/primary=c19OpenReplies'),
                        this.buildCountCard('pendingApprovals', 'Approval', 'Approval', 'c17Pending', '#Approval/list/primary=c17Pending'),
                    ],
                },
                {
                    key: 'researchStatus',
                    title: this.labels.researchStatus,
                    cards: [
                        this.buildCountCard('researchQueue', 'ProspectPool', 'ProspectPool', 'researchQueue', '#ProspectPool/list/primary=researchQueue'),
                        this.buildCountCard('followUpDue', 'Lead', 'Lead', 'peFollowUpDue', '#Lead/list/primary=peFollowUpDue'),
                        this.buildCountCard('researchRework', 'Lead', 'Lead', 'peResearchFailed', '#Lead/list/primary=peResearchFailed'),
                        this.buildCountCard('missingEvidence', 'Lead', 'Lead', 'peMissingEvidence', '#Lead/list/primary=peMissingEvidence'),
                    ],
                },
                {
                    key: 'outreachStatus',
                    title: this.labels.outreachStatus,
                    cards: [
                        this.buildCountCard('pendingOutreach', 'DraftApproval', 'DraftApproval', 'c17Pending', '#DraftApproval/list/primary=c17Pending'),
                        this.buildCountCard('sentAwaitingReply', 'ReplyEvent', 'ReplyEvent', 'c17AwaitingReply', '#ReplyEvent/list/primary=c17AwaitingReply'),
                    ],
                },
                {
                    key: 'commercialHandoff',
                    title: this.labels.commercialHandoff,
                    cards: [
                        this.buildCountCard('proposalReviewRequired', 'Lead', 'Lead', 'peProposalReviewRequired', '#Lead/list/primary=peProposalReviewRequired'),
                        this.buildHandoffCard('quoteCenterHandoff', 'Quote', '#Quote', this.labels.quoteCenterDescription),
                    ],
                },
            ];
        },

        buildPipelineConfigs: function () {
            return [
                this.buildPipelineStage('pipelineProspectPool', 'ProspectPool', null, '#ProspectPool'),
                this.buildPipelineStage('pipelineResearchInProgress', 'Lead', 'peResearchPending', '#Lead/list/primary=peResearchPending'),
                this.buildPipelineStage('pipelineResearched', 'Lead', 'peResearchCompleted', '#Lead/list/primary=peResearchCompleted'),
                this.buildPipelineStage('pipelineOutreached', 'Lead', 'peAwaitingReply', '#Lead/list/primary=peAwaitingReply'),
                this.buildPipelineStage('pipelineProposalReview', 'Lead', 'peProposalReviewRequired', '#Lead/list/primary=peProposalReviewRequired'),
            ];
        },

        buildCountCard: function (labelKey, scope, entityType, primaryFilter, href) {
            return {
                type: 'count',
                isCount: true,
                label: this.labels[labelKey],
                scope: scope,
                entityType: entityType,
                primaryFilter: primaryFilter,
                href: href,
                count: 0,
            };
        },

        buildHandoffCard: function (labelKey, scope, href, description) {
            return {
                type: 'handoff',
                isHandoff: true,
                label: this.labels[labelKey],
                scope: scope,
                href: href,
                description: description,
            };
        },

        buildPipelineStage: function (labelKey, entityType, primaryFilter, href) {
            return {
                label: this.labels[labelKey],
                entityType: entityType,
                primaryFilter: primaryFilter,
                href: href,
                count: 0,
            };
        },

        materializeSections: function () {
            var acl = this.getAcl();

            return this.sectionConfigs
                .map(function (section) {
                    var cards = section.cards.filter(function (card) {
                        return !card.scope || acl.check(card.scope, 'read');
                    }).map(function (card) {
                        return Object.assign({}, card);
                    });

                    return {
                        key: section.key,
                        title: section.title,
                        cards: cards,
                        hasCards: cards.length > 0,
                    };
                })
                .filter(function (section) {
                    return section.hasCards;
                });
        },

        materializePipeline: function () {
            var acl = this.getAcl();

            return this.pipelineConfigs
                .filter(function (stage) {
                    return acl.check(stage.entityType, 'read');
                })
                .map(function (stage) {
                    return Object.assign({}, stage);
                });
        },

        loadDashboardData: function () {
            var self = this;
            var sectionPromises = [];
            var pipelinePromises = [];

            this.sections.forEach(function (section, sectionIndex) {
                section.cards.forEach(function (card, cardIndex) {
                    if (card.type !== 'count') {
                        return;
                    }

                    sectionPromises.push(
                        self.countRecords(card.entityType, {primaryFilter: card.primaryFilter}).then(function (count) {
                            self.sections[sectionIndex].cards[cardIndex].count = count;
                        })
                    );
                });
            });

            this.pipeline.forEach(function (stage, stageIndex) {
                pipelinePromises.push(
                    self.countRecords(stage.entityType, {primaryFilter: stage.primaryFilter}).then(function (count) {
                        self.pipeline[stageIndex].count = count;
                    })
                );
            });

            return Promise.all(sectionPromises.concat(pipelinePromises)).then(function () {
                self.hasSections = self.sections.length > 0;
                self.hasPipeline = self.pipeline.length > 0;
                self.loading = false;
            }).catch(function () {
                self.sections = self.materializeSections();
                self.pipeline = self.materializePipeline();
                self.hasSections = self.sections.length > 0;
                self.hasPipeline = self.pipeline.length > 0;
                self.loading = false;
            });
        },

        countRecords: function (entityType, options) {
            var self = this;
            var settings = options || {};

            if (!this.getAcl().check(entityType, 'read')) {
                return Promise.resolve(0);
            }

            return new Promise(function (resolve) {
                self.getCollectionFactory().create(entityType, function (collection) {
                    collection.maxSize = 1;
                    collection.data = collection.data || {};

                    if (settings.primaryFilter) {
                        collection.data.primaryFilter = settings.primaryFilter;
                    }

                    collection.fetch()
                        .then(function () {
                            var total = collection.total;
                            resolve(typeof total === 'number' && total >= 0 ? total : 0);
                        })
                        .catch(function () {
                            resolve(0);
                        });
                });
            });
        },
    });
});
