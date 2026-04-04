# Impossible Puzzle

## 問題

長さが違うのに、同じ!?
```php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $A = $_POST['A'] ?? '';
    $B = $_POST['B'] ?? '';

    // type check
    if (!is_string($A) || !is_string($B)) {
        die('Invalid input');
    }
    // check
    if (strlen($A) != strlen($B) && $A == $B){
        echo "<blockquote>Congratulations! Here is your flag:\n" . getenv('FLAG') . "</blockquote>";
    }
    else {
        echo "<blockquote>Try again!</blockquote>";
    }
}
```
