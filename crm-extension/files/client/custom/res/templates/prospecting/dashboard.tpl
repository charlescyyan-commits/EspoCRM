<div class="row">
    <div class="col-sm-3">
        <div class="panel panel-default">
            <div class="panel-heading"><strong>Prospecting</strong></div>
            <div class="list-group list-group-panel">
                <a class="list-group-item active" href="#ProspectingDashboard">
                    <span class="fas fa-binoculars"></span> Prospecting Operations
                </a>
                <a class="list-group-item" data-action="open-search" href="#ProspectingSearch">
                    <span class="fas fa-search"></span> Search
                </a>
                <a class="list-group-item" href="#SearchJob">
                    <span class="fas fa-list"></span> Search Jobs
                </a>
                <a class="list-group-item" href="#ProspectPool">
                    <span class="fas fa-address-book"></span> Prospect Pool
                </a>
                <a class="list-group-item" href="#ResearchEvidence">
                    <span class="fas fa-flask"></span> Research Evidence
                </a>
                <a class="list-group-item" href="#SearchStrategy">
                    <span class="fas fa-sitemap"></span> Search Strategies
                </a>
            </div>
        </div>
        <div class="panel panel-default">
            <div class="panel-heading">Workflow</div>
            <div class="panel-body" style="font-size:12px;line-height:1.5;">
                <div>1. Plan a Search Strategy</div>
                <div>2. Run Search Jobs</div>
                <div>3. Review Prospect Pool</div>
                <div>4. Review Research Evidence</div>
            </div>
        </div>
    </div>
    <div class="col-sm-9">
        <div class="page-header" style="margin-top:0;">
            <h3 style="margin-top:0;">Prospecting Operations</h3>
            <p class="text-muted" style="margin-bottom:16px;">
                Discover customers, review candidates, and check research status.
            </p>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading"><strong>Prospecting Summary</strong></div>
            <div class="panel-body">
                {{#if loading}}
                    <div class="text-muted">Loading...</div>
                {{else}}
                    <div class="row">
                        {{#each metrics}}
                            <div class="col-sm-15" style="width:20%;float:left;padding:0 6px;box-sizing:border-box;">
                                <div class="text-center" style="padding:8px 4px;">
                                    <div class="text-muted" style="font-size:12px;">{{label}}</div>
                                    <div style="font-size:26px;font-weight:600;">
                                        <a href="{{href}}" style="color:inherit;text-decoration:none;">{{value}}</a>
                                    </div>
                                    {{#unless value}}
                                        <div class="text-muted" style="font-size:11px;">No data available</div>
                                    {{/unless}}
                                </div>
                            </div>
                        {{/each}}
                    </div>
                    <div class="clearfix"></div>
                    {{#unless hasMetrics}}
                        <div class="text-muted margin-top" style="margin-top:8px;">
                            No prospecting activity yet. Create a Search Strategy or start Discover to queue a Search Job.
                        </div>
                    {{/unless}}
                {{/if}}
            </div>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading">
                <strong>Recent Discovery Activity</strong>
                <a class="pull-right" href="#SearchJob" style="font-weight:normal;">View all</a>
            </div>
            <div class="panel-body" style="padding-top:0;">
                {{#if loading}}
                    <div class="text-muted" style="padding-top:12px;">Loading...</div>
                {{else}}
                    {{#if hasRecentJobs}}
                        <div class="table-responsive">
                            <table class="table table-striped" style="margin-bottom:0;">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Status</th>
                                        <th>Created</th>
                                        <th>Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {{#each recentJobs}}
                                        <tr>
                                            <td><a href="{{href}}">{{name}}</a></td>
                                            <td>{{status}}</td>
                                            <td>{{createdAt}}</td>
                                            <td>{{count}}</td>
                                        </tr>
                                    {{/each}}
                                </tbody>
                            </table>
                        </div>
                    {{else}}
                        <div class="text-muted" style="padding:16px 0;">
                            <div style="font-size:16px;margin-bottom:4px;">0</div>
                            No data available - no Search Jobs yet.
                            <div style="margin-top:8px;">
                                <a href="#ProspectingSearch">Start Discover</a>
                                |
                                <a href="#SearchStrategy">Open Search Strategies</a>
                            </div>
                        </div>
                    {{/if}}
                {{/if}}
            </div>
        </div>
    </div>
</div>
