define(['action-handler'], (Dep) => {
    return class extends Dep {
        async submitForReview() {
            await this.transition('submit-for-review', 'Quote submitted for review.');
        }

        async approve() {
            await this.transition('approve', 'Quote approved.');
        }

        async rejectReview() {
            const reason = prompt('Rejection reason (required):');
            if (!reason || !reason.trim()) {
                Espo.Ui.warning('A rejection reason is required.');
                return;
            }
            await this.transition('reject-review', 'Quote returned to draft.', {reason: reason.trim()});
        }

        async markCustomerRejected() {
            await this.transition('mark-customer-rejected', 'Quote rejected by customer.');
        }

        /**
         * @deprecated Backward-compat alias for markCustomerRejected.
         */
        async reject() {
            await this.transition('reject', 'Quote rejected.');
        }

        async sendQuote() {
            await this.transition('send', 'Quote sent.');
        }

        async markAccepted() {
            if (!confirm('Are you sure you want to mark this quote as accepted?')) {
                return;
            }
            await this.transition('mark-accepted', 'Quote accepted.');
        }

        async expire() {
            await this.transition('expire', 'Quote expired.');
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
                Espo.Ui.error(error.message || 'Unable to change Quote status.');
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
