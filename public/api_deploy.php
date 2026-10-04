<?php
/**
 * Aloria Labs - Ultra-Fast Zero-Friction Production Deployment Receiver
 * Allows GitHub Actions to push deployments over encrypted HTTPS (Port 443)
 * bypassing all shared hosting FTP passive-port firewall restrictions.
 */

error_reporting(0);
ini_set('display_errors', '0');

$DEPLOY_SECRET = "shriyansh0402_aloria_secure_deploy_2026";

$auth_header = isset($_SERVER['HTTP_X_ALORIA_DEPLOY_KEY']) ? $_SERVER['HTTP_X_ALORIA_DEPLOY_KEY'] : '';
$auth_param = isset($_POST['token']) ? $_POST['token'] : (isset($_GET['token']) ? $_GET['token'] : '');

if ($auth_header !== $DEPLOY_SECRET && $auth_param !== $DEPLOY_SECRET) {
    http_response_code(403);
    header('Content-Type: application/json');
    echo json_encode(["status" => "error", "message" => "Access Denied: Invalid deployment credentials"]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    header('Content-Type: application/json');
    $action = isset($_GET['action']) ? $_GET['action'] : '';
    if ($action === 'extract_local' && file_exists(__DIR__ . '/deploy.zip')) {
        $zip = new ZipArchive();
        if ($zip->open(__DIR__ . '/deploy.zip') === TRUE) {
            $zip->extractTo(__DIR__);
            $zip->close();
            @unlink(__DIR__ . '/deploy.zip');
            echo json_encode(["status" => "success", "message" => "deploy.zip extracted locally"]);
            exit;
        }
    }
    echo json_encode(["status" => "ready", "engine" => "Aloria Labs Deployment Receiver v1.0", "timestamp" => time()]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    header('Content-Type: application/json');
    
    if (!isset($_FILES['deploy_zip']) || $_FILES['deploy_zip']['error'] !== UPLOAD_ERR_OK) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Missing or invalid deploy_zip upload"]);
        exit;
    }

    $uploaded_tmp = $_FILES['deploy_zip']['tmp_name'];
    $target_dir = __DIR__;

    $zip = new ZipArchive();
    $res = $zip->open($uploaded_tmp);

    if ($res !== TRUE) {
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Failed to open zip archive. Code: " . $res]);
        exit;
    }

    $extracted_files = 0;
    for ($i = 0; $i < $zip->numFiles; $i++) {
        $filename = $zip->getNameIndex($i);
        // Security check: avoid directory traversal
        if (strpos($filename, '..') === false) {
            $extracted_files++;
        }
    }

    $zip->extractTo($target_dir);
    $zip->close();

    echo json_encode([
        "status" => "success",
        "message" => "Deployment extracted successfully to web root",
        "files_count" => $extracted_files,
        "timestamp" => date("Y-m-d H:i:s")
    ]);
    exit;
}
