<?php
/**
 * Aloria Labs - Ultra-Reliable Production Deployment Engine
 */
error_reporting(E_ALL);
ini_set('display_errors', '0');

$DEPLOY_SECRET = "shriyansh0402_aloria_secure_deploy_2026";
$token = $_REQUEST['token'] ?? ($_SERVER['HTTP_X_ALORIA_DEPLOY_KEY'] ?? '');

if ($token !== $DEPLOY_SECRET) {
    http_response_code(403);
    header('Content-Type: application/json');
    echo json_encode(["status" => "error", "message" => "Forbidden"]);
    exit;
}

header('Content-Type: application/json');
$extracted_frontend = false;
$extracted_backend = false;

// 1. Extract Frontend (deploy.zip)
$deploy_zip = __DIR__ . '/deploy.zip';
if (file_exists($deploy_zip)) {
    $zip = new ZipArchive();
    if ($zip->open($deploy_zip) === TRUE) {
        $zip->extractTo(__DIR__);
        $zip->close();
        @unlink($deploy_zip);
        $extracted_frontend = true;
    }
}

// 2. Extract Backend (aloria_python_backend.zip)
$backend_zip = __DIR__ . '/aloria_python_backend.zip';
if (file_exists($backend_zip)) {
    $api_dir = dirname(__DIR__) . '/aloria-api';
    if (!is_dir($api_dir)) {
        @mkdir($api_dir, 0755, true);
    }
    $zip = new ZipArchive();
    if ($zip->open($backend_zip) === TRUE) {
        $zip->extractTo($api_dir);
        $zip->close();
        @mkdir($api_dir . '/tmp', 0755, true);
        @touch($api_dir . '/tmp/restart.txt');
        $extracted_backend = true;
    }
}

echo json_encode([
    "status" => "success",
    "extracted_frontend" => $extracted_frontend,
    "extracted_backend" => $extracted_backend,
    "timestamp" => time()
]);
exit;
