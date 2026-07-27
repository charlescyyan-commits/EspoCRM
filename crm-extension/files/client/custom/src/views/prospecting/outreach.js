Espo.define('custom:views/prospecting/outreach', 'view', function (Dep) {
    return Dep.extend({
        template: 'custom:prospecting/outreach',

        setup: function () {
            this.loading = true;
            this.labels = this.buildLabels();
            this.sectionConfigs = this.buildSectionConfigs();
            this.sections = this.materializeSections();
            this.hasSections = this.sections.length > 0;
            this.wait(this.loadSectionCounts());
        },

        data: function () {
            return {
                loading: this.loading,
                labels: this.labels || {},
                sections: this.sections || [],
                hasSections: this.hasSections,
            };
        },

        buildLabels: function () {
            var translate = function (key) {
                return this.getLanguage().translate(key, 'labels', 'DraftApproval');
            }.bind(this);

            return {
                title: translate('outreachCenter'),
                subtitle: translate('workspaceDescription'),
                loading: translate('loading'),
                noData: translate('noData'),
                workspaceEmpty: translate('workspaceEmpty'),
                overview: translate('overview'),
                execution: translate('execution'),
                replyHandling: translate('replyHandling'),
                pendingApproval: translate('pendingApproval'),
                pendingApprovalDescription: translate('pendingApprovalDescription'),
                pendingSend: translate('pendingSend'),
                pendingSendDescription: translate('pendingSendDescription'),
                failedSend: translate('failedSend'),
                failedSendDescription: translate('failedSendDescription'),
                openReplies: translate('openReplies'),
                openRepliesDescription: translate('openRepliesDescription'),
                sendExecution: translate('sendExecution'),
                sendExecutionDescription: translate('sendExecutionDescription'),
                replyEvent: translate('replyEvent'),
                replyEventDescription: translate('replyEventDescription'),
                draftApproval: translate('draftApproval'),
                draftApprovalDescription: translate('draftApprovalDescription'),
            };
        },

        buildSectionConfigs: function () {
            return [
                {
                    key: 'overview',
                    title: this.labels.overview,
                    cards: [
                        this.buildCountCard(
                            'pendingApproval',
                            'DraftApproval',
                            'DraftApproval',
                            'c17Pending',
                            '#DraftApproval/list/primary=c17Pending',
                            this.labels.pendingApprovalDescription
                        ),
                        this.buildCountCard(
                            'pendingSend',
                            'SendExecution',
                            'SendExecution',
                            'c18ReadyToSend',
                            '#SendExecution/list/primary=c18ReadyToSend',
                            this.labels.pendingSendDescription
                        ),
                        this.buildCountCard(
                            'failedSend',
                            'SendExecution',
                            'SendExecution',
                            'c18FailedSend',
                            '#SendExecution/list/primary=c18FailedSend',
                            this.labels.failedSendDescription
                        ),
                        this.buildCountCard(
                            'openReplies',
                            'ReplyEvent',
                            'ReplyEvent',
                            'c19OpenReplies',
                            '#ReplyEvent/list/primary=c19OpenReplies',
                            this.labels.openRepliesDescription
                        ),
                    ],
                },
                {
                    key: 'execution',
                    title: this.labels.execution,
                    cards: [
                        this.buildCountCard(
                            'sendExecution',
                            'SendExecution',
                            'SendExecution',
                            null,
                            '#SendExecution',
                            this.labels.sendExecutionDescription
                        ),
                        this.buildCountCard(
                            'draftApproval',
                            'DraftApproval',
                            'DraftApproval',
                            null,
                            '#DraftApproval/list',
                            this.labels.draftApprovalDescription
                        ),
                    ],
                },
                {
                    key: 'replyHandling',
                    title: this.labels.replyHandling,
                    cards: [
                        this.buildCountCard(
                            'replyEvent',
                            'ReplyEvent',
                            'ReplyEvent',
                            null,
                            '#ReplyEvent',
                            this.labels.replyEventDescription
                        ),
                    ],
                },
            ];
        },

        buildCountCard: function (labelKey, scope, entityType, primaryFilter, href, description) {
            return {
                type: 'count',
                isCount: true,
                label: this.labels[labelKey],
                description: description,
                scope: scope,
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

        loadSectionCounts: function () {
            var self = this;
            var promises = [];

            this.sections.forEach(function (section, sectionIndex) {
                section.cards.forEach(function (card, cardIndex) {
                    promises.push(
                        self.countRecords(card.entityType, {primaryFilter: card.primaryFilter}).then(function (count) {
                            self.sections[sectionIndex].cards[cardIndex].count = count;
                        })
                    );
                });
            });

            return Promise.all(promises).then(function () {
                self.hasSections = self.sections.length > 0;
                self.loading = false;
            }).catch(function () {
                self.sections = self.materializeSections();
                self.hasSections = self.sections.length > 0;
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
