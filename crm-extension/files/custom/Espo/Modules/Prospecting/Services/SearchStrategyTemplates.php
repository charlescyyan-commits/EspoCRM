<?php

namespace Espo\Modules\Prospecting\Services;

final class SearchStrategyTemplates
{
    public const MAX_JOBS = 40;

    public const PRODUCTS = [
        'PlateCycler' => ['3D printer', 'Bambu Lab', '3D printing accessories', 'maker equipment', 'print farm supplier'],
        'Resin Tank' => ['resin 3D printer', 'SLA printer parts', '3D printing accessories', 'resin printer distributor'],
        'Filament Dryer' => ['filament 3D printer', '3D printing accessories', 'maker equipment', '3D printer store'],
        'Resin' => ['3D printing resin', 'SLA resin', 'dental 3D printing resin', 'resin printer supplies'],
        'LCD Replacement' => ['resin printer LCD', 'SLA printer parts', '3D printer replacement parts', '3D printing accessories'],
        'Mainboard' => ['3D printer mainboard', '3D printer electronics', '3D printer replacement parts', 'maker equipment'],
        'UV Meter' => ['UV meter 3D printing', 'resin printer equipment', 'SLA printer tools', '3D printing accessories'],
        'Heater' => ['3D printer heater', '3D printer replacement parts', 'industrial 3D printer parts', 'maker equipment'],
    ];

    public const PERSONAS = [
        'Distributor' => 'distributor',
        'Reseller' => 'reseller',
        'Dealer' => 'dealer',
        '3D Printer Store' => '3d printer store',
        'Print Farm' => 'print farm',
        'Service Provider' => 'service provider',
        'Education Supplier' => 'education supplier',
        'Dental Distributor' => 'dental distributor',
        'Industrial Distributor' => 'industrial distributor',
    ];

    public const SOURCES = [
        'GOOGLE_SEARCH',
        'GOOGLE_MAPS',
        'APIFY',
        'DIRECTORY',
        'CUSTOM_IMPORT',
        'CUSTOMS_DATA',
    ];
}
