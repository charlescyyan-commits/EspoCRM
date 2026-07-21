define(['action-handler'], (Dep) => {
    return class extends Dep {
        async submitForReview() {
            await this.transition('submit-for-review', 'Quote submitted for review.');
        }

        async approve() {
            await this.transition('approve', 'Quote approved.');
        }

        async reject() {
            await this.transition('reject', 'Quote rejected.');
        }

        async sendQuote() {
            await this.transition('send', 'Quote sent.');
        }

        async expire() {
            await this.transition('expire', 'Quote expired.');
        }

        isSubmitForReviewVisible() {
            return this.isStatus('DRAFT');
        }

        isApproveVisible() {
            return this.isStatus('IN_REVIEW');
        }

        isRejectVisible() {
            return this.isStatus('IN_REVIEW');
        }

        isSendQuoteVisible() {
            return this.isStatus('APPROVED');
        }

        isExpireVisible() {
            return this.isStatus('APPROVED');
        }

        isStatus(status) {
            return this.view.model.get('status') === status;
        }

        async transition(action, successMessage) {
            this.view.disableMenuItem(this.menuItemName(action));

            try {
                await Espo.Ajax.postRequest(
                    'Prospecting/quote/' + encodeURIComponent(this.view.model.id) + '/workflow/' + action
                );
                await this.view.model.fetch();
                Espo.Ui.success(successMessage);
            } catch (error) {
                Espo.Ui.error(error.message || 'Unable to change Quote status.');
            } finally {
                this.view.enableMenuItem(this.menuItemName(action));
            }
        }

        menuItemName(action) {
            return {
                'submit-for-review': 'submitForReview',
                approve: 'approveQuote',
                reject: 'rejectQuote',
                send: 'sendQuote',
                expire: 'expireQuote',
            }[action];
        }
    };
});
