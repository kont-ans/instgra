<?php
/**
 * Ultra Download - Robust API Bridge & Download Proxy
 * وظيفته: تجاوز مشكلة CORS والحظر، وتوفير بروكسي للتحميل المباشر مع إجبار اللاحقة (mp4/mp3)
 */

// 1. السماح بـ CORS
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// 2. وضع التحميل المباشر (Proxy Download)
if (isset($_GET['download_url'])) {
    $download_url = $_GET['download_url'];
    $filename = isset($_GET['filename']) ? $_GET['filename'] : 'Ultra_Download';
    $ext = isset($_GET['ext']) ? $_GET['ext'] : '';

    // تنظيف اسم الملف
    $filename = preg_replace('/[^A-Za-z0-9_\-]/', '_', $filename);
    
    // تحديد اللاحقة والـ Content-Type بدقة
    $content_type = 'application/octet-stream';
    if (empty($ext)) {
        // محاولة استنتاج اللاحقة من الرابط إذا لم يتم تمريرها
        if (strpos($download_url, 'audio') !== false || strpos($download_url, '.mp3') !== false) {
            $ext = 'mp3';
            $content_type = 'audio/mpeg';
        } else {
            $ext = 'mp4';
            $content_type = 'video/mp4';
        }
    } else {
        // استخدام اللاحقة الممررة وتحديد الـ Content-Type المناسب
        $ext = strtolower($ext);
        if ($ext == 'mp3' || $ext == 'm4a') {
            $content_type = 'audio/mpeg';
        } elseif ($ext == 'mp4' || $ext == 'webm') {
            $content_type = 'video/mp4';
        }
    }

    // بناء اسم الملف النهائي مع اللاحقة
    $final_filename = $filename . '.' . $ext;

    // استخدام cURL لجلب رؤوس الملف أولاً لمعرفة الحجم
    $ch_head = curl_init();
    curl_setopt($ch_head, CURLOPT_URL, $download_url);
    curl_setopt($ch_head, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch_head, CURLOPT_HEADER, true);
    curl_setopt($ch_head, CURLOPT_NOBODY, true);
    curl_setopt($ch_head, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch_head, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch_head, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36');
    curl_exec($ch_head);
    $file_size = curl_getinfo($ch_head, CURLINFO_CONTENT_LENGTH_DOWNLOAD);
    curl_close($ch_head);

    // إرسال رؤوس التحميل الصارمة
    header('Content-Description: File Transfer');
    header('Content-Type: ' . $content_type);
    header('Content-Disposition: attachment; filename="' . $final_filename . '"');
    header('Content-Transfer-Encoding: binary');
    header('Expires: 0');
    header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
    header('Pragma: public');
    
    if ($file_size > 0) {
        header('Content-Length: ' . $file_size);
    }

    // استخدام cURL لقراءة الملف وإرساله مباشرة للمتصفح (Stream)
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $download_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, false); 
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36');
    
    curl_exec($ch);
    curl_close($ch);
    exit;
}

// 3. وضع جلب البيانات (API Fetch)
header("Content-Type: application/json; charset=UTF-8");
$video_url = isset($_GET['url']) ? $_GET['url'] : '';

if (empty($video_url)) {
    echo json_encode(["error" => "يرجى توفير رابط صالح.", "status" => "error"]);
    exit;
}

$api_url = "https://sii3.top/api/download.php?url=" . urlencode($video_url);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36');

$response = curl_exec($ch);
curl_close($ch);

if ($response) {
    $decoded = json_decode($response);
    if (json_last_error() === JSON_ERROR_NONE) {
        echo json_encode($decoded);
    } else {
        echo json_encode(["error" => "لم يتم العثور على روابط تحميل. تأكد من صحة الرابط.", "status" => "error"]);
    }
} else {
    echo json_encode(["error" => "لم يتم استلام بيانات من المصدر.", "status" => "error"]);
}
?>
