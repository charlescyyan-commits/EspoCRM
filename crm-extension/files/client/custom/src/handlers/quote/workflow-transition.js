define(['action-handler'], (Dep) => {
    return class extends Dep {
        async submitForReview() {
            await this.transition('submit-for-review', this.translate('quoteSubmittedForReview'));
        }

        async approve() {
            await this.transition('approve', this.translate('quoteApproved'));
        }

        async rejectReview() {
            const reason = prompt(this.translate('rejectionReasonPrompt'));
            if (!reason || !reason.trim()) {
                Espo.Ui.warning(this.translate('rejectionReasonRequired'));
                return;
            }
            await this.transition('reject-review', this.translate('quoteReturnedToDraft'), {reason: reason.trim()});
        }

        async markCustomerRejected() {
            await this.transition('mark-customer-rejected', this.translate('quoteRejectedByCustomer'));
        }

        /**
         * @deprecated Backward-compat alias for markCustomerRejected.
         */
        async reject() {
            await this.transition('reject', this.translate('quoteRejected'));
        }

        async sendQuote() {
            await this.transition('send', this.translate('quoteSent'));
        }

        async markAccepted() {
            if (!confirm(this.translate('markAcceptedConfirmation'))) {
                return;
            }
            await this.transition('mark-accepted', this.translate('quoteAccepted'));
        }

        async expire() {
            await this.transition('expire', this.translate('quoteExpired'));
        }

        // ----------------------------------------------------------
        // Visibility
        // ----------------------------------------------------------

        isSubmitForReviewVisible() {
            return this.isStatus('DRAFT');
        }

        isApproveVisible() {
            return this.isStatus('IN_REVIEW');
        }

        isRejectReviewVisible() {
            return this.isStatus('IN_REVIEW');
        }

        isMarkCustomerRejectedVisible() {
            return this.isStatus('SENT');
        }

        isRejectVisible() {
            return this.isStatus('SENT');
        }

        isSendQuoteVisible() {
            return this.isStatus('APPROVED');
        }

        isExpireVisible() {
            return this.isStatus('APPROVED');
        }

        isMarkAcceptedVisible() {
            return this.isStatus('SENT');
        }

        // ----------------------------------------------------------
        // Helpers
        // ----------------------------------------------------------

        isStatus(status) {
            return this.view.model.get('status') === status;
        }

        translate(key) {
            return this.view.getLanguage().translate(key, 'labels', 'Quote');
        }

        async transition(action, successMessage, extraData) {
            this.view.disableMenuItem(this.menuItemName(action));

            try {
                await Espo.Ajax.postRequest(
                    'Prospecting/quote/' + encodeURIComponent(this.view.model.id) + '/workflow/' + action,
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
                'submit-for-review': 'submitForReview',
                approve: 'approveQuote',
                'reject-review': 'rejectReviewQuote',
                'mark-customer-rejected': 'markCustomerRejectedQuote',
                reject: 'rejectQuote',
                send: 'sendQuote',
                'mark-accepted': 'markAcceptedQuote',
                expire: 'expireQuote',
            }[action];
        }
    };
});
