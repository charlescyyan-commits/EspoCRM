define(['action-handler'], (Dep) => {
    return class extends Dep {
        async approve() {
            if (!confirm(this.translate('approveConfirmation'))) {
                return;
            }

            await this.decide('approve', this.translate('approvalRecorded'));
        }

        async deny() {
            const reason = prompt(this.translate('denialReasonPrompt'));
            if (!reason || !reason.trim()) {
                Espo.Ui.warning(this.translate('denialReasonRequired'));
                return;
            }

            await this.decide(
                'deny',
                this.translate('denialRecorded'),
                {reason: reason.trim()}
            );
        }

        async defer() {
            const reason = prompt(this.translate('deferReasonPrompt'));

            await this.decide(
                'defer',
                this.translate('deferRecorded'),
                reason && reason.trim() ? {reason: reason.trim()} : {}
            );
        }

        isDecisionVisible() {
            return this.view.model.get('decision') === 'PENDING'
                && this.view.getAcl().check('ActionGate', 'edit');
        }

        async decide(action, successMessage, data) {
            const menuItem = {
                approve: 'approveActionGate',
                deny: 'denyActionGate',
                defer: 'deferActionGate',
            }[action];

            this.view.disableMenuItem(menuItem);
            try {
                await Espo.Ajax.postRequest(
                    'Prospecting/action-gate/'
                        + encodeURIComponent(this.view.model.id)
                        + '/decision/'
                        + action,
                    data || {}
                );
                await this.view.model.fetch();
                Espo.Ui.success(successMessage);
            } catch (error) {
                Espo.Ui.error(
                    error.message || this.translate('decisionFailed')
                );
            } finally {
                this.view.enableMenuItem(menuItem);
            }
        }

        translate(key) {
            return this.view
                .getLanguage()
                .translate(key, 'labels', 'ActionGate');
        }
    };
});
