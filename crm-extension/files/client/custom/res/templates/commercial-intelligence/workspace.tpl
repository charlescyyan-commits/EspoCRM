<div class="c25-workspace" data-c25-surface="commercial-intelligence-workspace">
    <div class="page-header" style="margin-top: 0;">
        <h3 style="margin-top: 0;">Commercial Intelligence Workspace</h3>
        <!-- D2: AI/assembled marker — visually distinct from CRM records, source evidence, and human decisions -->
        <span class="label label-warning c25-ai-assembled" data-c25-marker="ai-assembled">
            AI / Assembled — {{advisoryDesignation}}
        </span>
    </div>

    {{#if loading}}
        <div class="panel panel-default">
            <div class="panel-body text-muted">Loading…</div>
        </div>
    {{else}}
        {{#unless hasAnchor}}
            <div class="panel panel-default">
                <div class="panel-body text-muted">
                    Open this workspace from an OpportunityCandidate to assemble its commercial context.
                </div>
            </div>
        {{/unless}}

        {{#if error}}
            <div class="panel panel-danger">
                <div class="panel-body">
                    Commercial context could not be assembled or is not visible to you.
                </div>
            </div>
        {{/if}}

        {{#if hasContext}}
            <!-- Assembled intelligence region (AI / advisory only) -->
            <div class="c25-assembled-region" data-c25-region="assembled-intelligence">
                {{#if hasSections}}
                    {{#each sections}}
                        <div class="panel panel-default c25-evidence-panel" data-c25-section="{{key}}">
                            <div class="panel-heading">
                                <strong>{{title}}</strong>
                                <span class="label label-warning c25-ai-assembled pull-right" data-c25-marker="ai-assembled">AI / Assembled</span>
                            </div>
                            <div class="panel-body">
                                <table class="table table-condensed">
                                    <thead>
                                        <tr>
                                            <th>Source</th>
                                            <th>Revision</th>
                                            <th>Freshness</th>
                                            <th>Validation state</th>
                                            <th>Evidence</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {{#each references}}
                                            <tr class="{{#if stalenessWarning}}c25-stale-warning{{/if}}">
                                                <td>
                                                    {{entityType}}{{#if displayName}} · {{displayName}}{{/if}}
                                                    <div class="text-muted" style="font-size: 11px;">{{layer}}</div>
                                                </td>
                                                <td class="text-muted">{{revision}}</td>
                                                <td>
                                                    {{freshnessStatus}}
                                                    {{#if stalenessWarning}}
                                                        <span class="label label-default c25-freshness-warning">{{warningLabel}}</span>
                                                    {{/if}}
                                                </td>
                                                <td>{{validationState}}</td>
                                                <td>
                                                    {{#if isNavigable}}
                                                        <!-- D2: bounded one-click navigation to source evidence -->
                                                        <a href="{{navigationReference}}" class="c25-evidence-link" data-c25-action="source-navigation">
                                                            Source evidence
                                                        </a>
                                                    {{else}}
                                                        <span class="text-muted c25-evidence-unavailable" data-c25-action="source-unavailable">
                                                            Source evidence unavailable
                                                        </span>
                                                    {{/if}}
                                                </td>
                                            </tr>
                                        {{/each}}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    {{/each}}
                {{else}}
                    <div class="panel panel-default">
                        <div class="panel-body text-muted">No governed evidence is linked to this candidate yet.</div>
                    </div>
                {{/if}}
            </div>

            <!-- D2: visible boundary divider between AI-assembled interpretation and CRM business records -->
            <div class="c25-boundary-divider" data-c25-marker="boundary-divider" role="separator" style="border-top: 2px solid #d9534f; margin: 24px 0; text-align: center;">
                <span class="c25-boundary-label label label-danger">
                    Assembled intelligence above — CRM business records below
                </span>
            </div>

            <!-- Source-native region: read-only navigation only, never edited here -->
            <div class="c25-crm-region" data-c25-region="crm-records">
                <p class="text-muted">
                    CRM business records open in their own surfaces. This workspace never edits them.
                </p>
            </div>

            <!-- Entry slots: placeholders only — WP2 Brief and WP3 Assistant are not implemented -->
            <div class="c25-entry-slots" data-c25-region="entry-slots" style="margin-top: 16px;">
                <span class="label label-default c25-entry-slot" data-c25-slot="assistant" style="margin-right: 8px;">
                    Revenue Analyst Assistant (upcoming)
                </span>
                <span class="label label-default c25-entry-slot" data-c25-slot="brief">
                    AI Commercial Brief (upcoming)
                </span>
            </div>
        {{/if}}
    {{/if}}
</div>
