<div class="page-header" style="margin-top: 0;">
    <h3 style="margin-top: 0;">{{labels.title}}</h3>
    <p class="text-muted">{{labels.description}}</p>
</div>

{{#if loading}}
    <div class="panel panel-default">
        <div class="panel-body text-muted">{{labels.loading}}</div>
    </div>
{{else}}
    {{#if hasCards}}
        <div class="row">
            {{#each cards}}
                <div class="col-sm-6 col-md-3">
                    <div class="panel panel-default">
                        <div class="panel-body">
                            <div class="text-muted">{{label}}</div>
                            <div style="font-size: 30px; font-weight: 600;">
                                <a href="{{href}}">{{count}}</a>
                            </div>
                            {{#unless count}}
                                <small class="text-muted">
                                    {{../labels.noData}}
                                </small>
                            {{/unless}}
                        </div>
                    </div>
                </div>
            {{/each}}
        </div>
    {{else}}
        <div class="panel panel-default">
            <div class="panel-body text-muted">{{labels.empty}}</div>
        </div>
    {{/if}}

    {{#if canReadLedger}}
        <div class="panel panel-default">
            <div class="panel-heading">
                <strong>{{labels.ledgerTimeline}}</strong>
            </div>
            <div class="panel-body">
                <p class="text-muted">{{labels.ledgerDescription}}</p>
                <a class="btn btn-default" href="#ExecutionLedger">
                    {{labels.ledgerTimeline}}
                </a>
                <a
                    class="btn btn-default"
                    href="#ExecutionLedger/list/primary=executionFailures"
                >
                    {{labels.failureReview}}
                </a>
            </div>
        </div>
    {{/if}}
{{/if}}
