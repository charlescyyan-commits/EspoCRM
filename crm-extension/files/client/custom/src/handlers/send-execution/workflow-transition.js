define(['action-handler'], (Dep) => {
    return class extends Dep {
        async retry() {
            await this.transition('retry', this.translate('retrySucceeded'));
        }

        async cancel() {
            const reason = prompt(this.translate('cancelReasonPrompt'));
            if (!this.isValidCancelReason(reason)) {
                Espo.Ui.warning(this.translate('cancelReasonRequired'));
                return;
            }
            await this.transition('cancel', this.translate('cancelSucceeded'), {
                reason: reason.trim().toUpperCase(),
            });
        }

        async ignore() {
            if (!confirm(this.translate('ignoreConfirmation'))) {
                return;
            }
            await this.transition('ignore', this.translate('ignoreSucceeded'), {
                reason: 'IGNORED',
            });
        }

        isRetryVisible() {
            return this.isFailed() && this.retryCount() < this.maxRetries();
        }

        isCancelVisible() {
            return this.isFailed();
        }

        isIgnoreVisible() {
            return this.isFailed();
        }

        isFailed() {
            return this.view.model.get('status') === 'FAILED';
        }

        retryCount() {
            return Number(this.view.model.get('retryCount') || 0);
        }

        maxRetries() {
            return Number(this.view.model.get('maxRetries') || 0);
        }

        isValidCancelReason(reason) {
            return ['ABANDONED', 'DUPLICATE', 'OTHER'].includes(String(reason || '').trim().toUpperCase());
        }

        translate(key) {
            return this.view.getLanguage().translate(key, 'labels', 'SendExecution');
        }

        async transition(action, successMessage, extraData) {
            this.view.disableMenuItem(this.menuItemName(action));

            try {
                await Espo.Ajax.postRequest(
                    'Prospecting/send-execution/' + encodeURIComponent(this.view.model.id) + '/workflow/' + action,
                    extraData || {}
                );
                await this.view.model.fetch();
                Espo.Ui.success(successMessage);
            } catch (error) {
                Espo.Ui.error(error.message || this.translate('statusChangeFailed'));
            } finally {
                this.view.enableMenuItem(this.menuItemName(action));
            }
        }

        menuItemName(action) {
            return {
                retry: 'retrySendExecution',
                cancel: 'cancelSendExecution',
                ignore: 'ignoreSendExecution',
            }[action];
        }
    };
});
