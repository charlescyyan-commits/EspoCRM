<?php

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Exceptions\NotFound;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use stdClass;

class SearchStrategyService
{
    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    public function generate(stdClass $body): array
    {
        $strategyId = trim((string) ($body->strategyId ?? ''));
        if ($strategyId === '') {
            throw new BadRequest('Missing strategyId.');
        }

        $strategy = $this->entityManager->getEntityById('SearchStrategy', $strategyId);
        if (!$strategy) {
            throw new NotFound('Search Strategy was not found.');
        }
        if (!$this->acl->checkEntityEdit($strategy)) {
            throw new Forbidden();
        }
        if ($strategy->get('status') === 'CANCELLED') {
            throw new BadRequest('Cancelled Search Strategy cannot generate Discovery Jobs.');
        }

        $candidates = $this->expand($strategy);
        $created = 0;
        $existing = 0;
        $strategyJobCount = 0;

        foreach ($candidates as $candidate) {
            $job = $this->entityManager->getRDBRepository('SearchJob')
                ->where(['queryFingerprint' => $candidate['queryFingerprint']])
                ->findOne();
            if ($job) {
                $existing++;
                if ($job->get('strategyId') === $strategy->getId()) {
                    $strategyJobCount++;
                }
                continue;
            }

            if (!$this->acl->check('SearchJob', 'create')) {
                throw new Forbidden();
            }

            $job = $this->entityManager->getEntity('SearchJob');
            $job->set([
                'name' => $candidate['keyword'] . ' [' . $candidate['source'] . ']',
                'strategyId' => $strategy->getId(),
                'product' => $candidate['product'],
                'keyword' => $candidate['keyword'],
                'country' => $candidate['country'],
                'source' => $candidate['source'],
                'status' => 'QUEUED',
                'priority' => 'P2',
                'queryFingerprint' => $candidate['queryFingerprint'],
                'resultCount' => 0,
                'acceptedCount' => 0,
                'rejectedCount' => 0,
                'assignedUserId' => $strategy->get('assignedUserId'),
            ]);
            $this->entityManager->saveEntity($job);
            $created++;
            $strategyJobCount++;
        }

        $strategy->set([
            'status' => 'GENERATED',
            'generatedJobCount' => $strategyJobCount,
        ]);
        $this->entityManager->saveEntity($strategy);

        return [
            'success' => true,
            'strategy_id' => $strategy->getId(),
            'status' => 'GENERATED',
            'generated_count' => $created,
            'existing_count' => $existing,
            'generated_job_count' => $strategyJobCount,
            'max_jobs' => SearchStrategyTemplates::MAX_JOBS,
        ];
    }

    private function expand(Entity $strategy): array
    {
        $product = trim((string) $strategy->get('product'));
        $country = trim((string) $strategy->get('country'));
        if ($product === '' || !isset(SearchStrategyTemplates::PRODUCTS[$product])) {
            throw new BadRequest('Unsupported or missing product.');
        }
        if ($country === '') {
            throw new BadRequest('Missing country.');
        }

        $personas = $this->multiValue($strategy->get('targetPersona'));
        if ($personas === []) {
            throw new BadRequest('Missing targetPersona.');
        }
        foreach ($personas as $persona) {
            if (!isset(SearchStrategyTemplates::PERSONAS[$persona])) {
                throw new BadRequest('Unsupported targetPersona: ' . $persona . '.');
            }
        }

        $sources = $this->multiValue($strategy->get('sourcePlan'));
        if ($sources === []) {
            throw new BadRequest('Missing sourcePlan.');
        }
        foreach ($sources as $source) {
            if (!in_array($source, SearchStrategyTemplates::SOURCES, true)) {
                throw new BadRequest('Unsupported sourcePlan entry: ' . $source . '.');
            }
        }

        $terms = array_merge(SearchStrategyTemplates::PRODUCTS[$product], $this->lines((string) $strategy->get('keywords')));
        $excluded = array_fill_keys(array_map($this->normalize(...), $this->lines((string) $strategy->get('excludedKeywords'))), true);
        $companyType = trim((string) $strategy->get('targetCompanyType'));
        $candidates = [];

        foreach ($terms as $term) {
            if (isset($excluded[$this->normalize($term)])) {
                continue;
            }
            foreach ($personas as $persona) {
                $keyword = trim(implode(' ', array_filter([
                    $term,
                    SearchStrategyTemplates::PERSONAS[$persona],
                    $companyType,
                    $country,
                ])));
                foreach ($sources as $source) {
                    $fingerprint = $this->fingerprint($product, $country, $keyword, $source);
                    $candidates[$fingerprint] = [
                        'product' => $product,
                        'country' => $country,
                        'keyword' => $keyword,
                        'source' => $source,
                        'queryFingerprint' => $fingerprint,
                    ];
                    if (count($candidates) > SearchStrategyTemplates::MAX_JOBS) {
                        throw new BadRequest('Search Strategy exceeds maximum Discovery Job count of ' . SearchStrategyTemplates::MAX_JOBS . '.');
                    }
                }
            }
        }

        return array_values($candidates);
    }

    private function multiValue(mixed $value): array
    {
        if (is_array($value)) {
            return array_values(array_filter(array_map('trim', $value)));
        }
        if (!is_string($value) || trim($value) === '') {
            return [];
        }
        $decoded = json_decode($value, true);
        if (is_array($decoded)) {
            return array_values(array_filter(array_map('trim', $decoded)));
        }
        return array_values(array_filter(array_map('trim', explode(',', $value))));
    }

    private function lines(string $value): array
    {
        return array_values(array_unique(array_filter(array_map('trim', preg_split('/[\r\n,]+/', $value) ?: []))));
    }

    private function fingerprint(string $product, string $country, string $keyword, string $source): string
    {
        return hash('sha256', implode('|', [
            $this->normalize($product),
            $this->normalize($country),
            $this->normalize($keyword),
            $this->normalize($source),
        ]));
    }

    private function normalize(string $value): string
    {
        return strtolower(trim((string) preg_replace('/\s+/', ' ', $value)));
    }
}
