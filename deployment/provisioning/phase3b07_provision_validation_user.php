<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$role = $entityManager->getRDBRepository('Role')->where(['name' => 'Integration Bot'])->findOne();
if (!$role) {
    throw new \RuntimeException('Integration Bot role is required.');
}

$user = $entityManager->getRDBRepository('User')->where(['userName' => 'phase3b07_validation_bot'])->findOne();
if (!$user) {
    $user = $entityManager->getEntity('User');
    $user->set('userName', 'phase3b07_validation_bot');
}
$user->set('lastName', 'Phase3B07 Validation Bot');
$user->set('type', 'api');
$user->set('isActive', true);
$user->set('authMethod', 'ApiKey');
$user->set('apiKey', 'phase3b07-local-test-api-key');
$entityManager->saveEntity($user);

$relation = $entityManager->getRDBRepository('User')->getRelation($user, 'roles');
if (!$relation->where(['id' => $role->getId()])->findOne()) {
    $relation->relateById($role->getId());
}

echo "PHASE3B07_VALIDATION_USER_READY\n";
