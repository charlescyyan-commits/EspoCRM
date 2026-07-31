<div class="c25-source-detail" data-c25-surface="governed-source-detail">
    <div class="page-header" style="margin-top: 0;">
        <a href="{{backHref}}" class="text-muted c25-source-back" data-c25-action="back-to-workspace">
            &larr; Back to Commercial Intelligence Workspace
        </a>
        <h3 style="margin: 12px 0 8px;">Governed Source Evidence</h3>
        <span class="label label-warning" data-c25-marker="read-only-governed-source">
            Read-only governed source
        </span>
        <span class="label label-danger" data-c25-marker="truth-boundary">
            Source evidence — not assembled CRM truth
        </span>
    </div>

    {{#if loading}}
        <div class="panel panel-default">
            <div class="panel-body text-muted">Loading governed source…</div>
        </div>
    {{else}}
        {{#if error}}
            <div class="panel panel-danger">
                <div class="panel-body">
                    This governed source is unavailable or is not visible to you.
                </div>
            </div>
        {{/if}}

        {{#if hasSource}}
            <div class="panel panel-default">
                <div class="panel-heading">
                    <strong>{{source.entityType}}</strong>
                    {{#if source.displayName}} · {{source.displayName}}{{/if}}
                </div>
                <div class="panel-body">
                    <dl class="dl-horizontal c25-source-identity">
                        <dt>Entity type</dt>
                        <dd>{{source.entityType}}</dd>
                        <dt>Record ID</dt>
                        <dd><code>{{source.entityId}}</code></dd>
                        <dt>Designation</dt>
                        <dd>{{source.designation}}</dd>
                    </dl>

                    {{#if hasFields}}
                        <div class="table-responsive">
                            <table class="table table-condensed c25-source-fields">
                                <thead>
                                    <tr>
                                        <th style="width: 28%;">Field</th>
                                        <th>Evidence value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {{#each fields}}
                                        <tr data-c25-field="{{name}}">
                                            <th>{{label}}</th>
                                            <td style="white-space: pre-wrap; overflow-wrap: anywhere;">{{value}}</td>
                                        </tr>
                                    {{/each}}
                                </tbody>
                            </table>
                        </div>
                    {{else}}
                        <p class="text-muted">No review fields are available for this source.</p>
                    {{/if}}
                </div>
            </div>
        {{/if}}
    {{/if}}

    <p class="text-muted" style="margin-top: 16px;">
        This surface supports evidence review only. Lifecycle and CRM mutation remain with the owning layer.
    </p>
</div>
