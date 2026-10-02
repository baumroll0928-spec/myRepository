# C# File-based app

## 問題

.NET 10で追加されたFile-based apps機能のおかげで、.csファイルそのものを実行できるようになりました！

```cs
Console.Write("flag> ");
Console.Out.Flush();
string input = Console.ReadLine()?.Trim() ?? "";
Console.WriteLine(IsCorrect() ? $"Correct! The flag is {input}" : "Incorrect...");

bool IsCorrect()
{
    ReadOnlySpan<byte> encoded = "GzMA+MVtbG/XtFYgGNGLSpSiwoAdaiYvxraqBw=="u8;
    Span<byte> temp1 = stackalloc byte[256];
    Base64.DecodeFromUtf8(encoded, temp1, out _, out int bytesWritten1);

    Span<byte> temp2 = stackalloc byte[256];
    using var decoder = new BrotliDecoder();
    decoder.Decompress(temp1[..bytesWritten1], temp2, out _, out int bytesWritten2);

    Span<byte> temp3 = stackalloc byte[Encoding.UTF8.GetMaxByteCount(input.Length)];
    int bytesWritten3 = Encoding.UTF8.GetBytes(input, temp3);
    return temp2[..bytesWritten2].SequenceEqual(temp3[..bytesWritten3]);
}
```

## 概要

.NET 10で.csを実行できるようになったとのことで、これを利用したフラグチェッカーのようです。

## Windowsでの実行について

配付の`run-using-docker.sh`はWindowsではそのまま実行できなかったので、ちょっとだけ書き換えました。

### Powershell用 (run.ps1)
```ps1
docker run --interactive --tty --rm --volume="${PWD}:/app" `
    mcr.microsoft.com/dotnet/sdk:10.0@sha256:2fa828c68761b1b8c23d7662dc134421b9d3b59fe1425fdbc80804e390cdb24d `
    dotnet run -p:PublishAot=false /app/chal.cs
```
### コマンドプロンプト用 (run.cmd)
```cmd
docker run --interactive --tty --rm --volume="%cd%:/app" ^
    mcr.microsoft.com/dotnet/sdk:10.0@sha256:2fa828c68761b1b8c23d7662dc134421b9d3b59fe1425fdbc80804e390cdb24d ^
    dotnet run -p:PublishAot=false /app/chal.cs
```

## 解法

`chal.cs`を見てみると、フラグを入力させた後、`bool IsCorrect()`関数を呼び出して、`true`が返ったら`Correct!`、`false`が返ったら`Incorrect...`と表示するようになっています。

よって、この問題の目的は`IsCorrect`関数が`true`を返すような入力を見つけることだとわかります。

では、`IsCorrect`関数で何をしているか順番に見ていくことにしましょう。

```cs
    ReadOnlySpan<byte> encoded = "GzMA+MVtbG/XtFYgGNGLSpSiwoAdaiYvxraqBw=="u8;
    Span<byte> temp1 = stackalloc byte[256];
    Base64.DecodeFromUtf8(encoded, temp1, out _, out int bytesWritten1);
```
`Base64.DecodeFromUtf8(encoded, temp1, out _, out int bytesWritten1);`は、UTF8の`encoded`をBase64デコードした結果を`temp1`に出力し、出力バイト数を`bytesWritten1`に出力します。[参考](https://learn.microsoft.com/ja-jp/dotnet/api/system.buffers.text.base64.decodefromutf8?view=net-10.0)

```cs
    Span<byte> temp2 = stackalloc byte[256];
    using var decoder = new BrotliDecoder();
    decoder.Decompress(temp1[..bytesWritten1], temp2, out _, out int bytesWritten2);
```
`decoder.Decompress(temp1[..bytesWritten1], temp2, out _, out int bytesWritten2);`は、brotliという形式で圧縮された`temp1[..bytesWritten1]`を展開した結果を`temp2`に出力し、出力バイト数を`bytesWritten2`に出力します。
[参考](https://learn.microsoft.com/ja-jp/dotnet/api/system.io.compression.brotlidecoder.decompress?view=net-10.0)

```cs
    Span<byte> temp3 = stackalloc byte[Encoding.UTF8.GetMaxByteCount(input.Length)];
    int bytesWritten3 = Encoding.UTF8.GetBytes(input, temp3);
    return temp2[..bytesWritten2].SequenceEqual(temp3[..bytesWritten3]);
```
`temp2[..bytesWritten2].SequenceEqual(temp3[..bytesWritten3])`は、`temp2[..bytesWritten2]`と入力をバイト列に変換した`temp3[..bytesWritten3]`を比較し、等しい場合は`true`、等しくない場合は`false`を返します。
[参考](https://learn.microsoft.com/ja-jp/dotnet/api/system.linq.enumerable.sequenceequal?view=net-10.0)

これをreturnしているので、まとめると、展開結果と入力が同じ場合に`IsCorrect`関数は`true`を返すことがわかりました。

なので、展開結果`temp2`の内容が知りたいところですね。

## ソルバー

前述のとおり`.Decompress`したあと正解のフラグが`temp2`に入っているはずなので、そこまではまるっとコピペし、`temp2`の内容を出力するようにしてみます。

```cs
using System.Buffers.Text;
using System.IO.Compression;
using System.Text;

ReadOnlySpan<byte> encoded = "GzMA+MVtbG/XtFYgGNGLSpSiwoAdaiYvxraqBw=="u8;
Span<byte> temp1 = stackalloc byte[256];
Base64.DecodeFromUtf8(encoded, temp1, out _, out int bytesWritten1);

Span<byte> temp2 = stackalloc byte[256];
using var decoder = new BrotliDecoder();
decoder.Decompress(temp1[..bytesWritten1], temp2, out _, out int bytesWritten2);

string flag = Encoding.UTF8.GetString(temp2[..bytesWritten2]);
Console.WriteLine(flag);
```
これによって得られたフラグ`Alpaca{...}`を、配布のプログラムを実行して入力すると、正しいことが確認できました。

なお、Pythonで解くならこんな感じになります。

```py
import base64
import brotli # pip install brotli

encoded = "GzMA+MVtbG/XtFYgGNGLSpSiwoAdaiYvxraqBw=="
temp1 = base64.b64decode(encoded)
temp2 = brotli.decompress(temp1)
print(temp2.decode())
```

## その他

今日は総務省主催の「全国型CTFコンテスト」ですね。

私も`Online1478_baumroll1234`で参加します。他にも参加される方がいたら一緒に頑張りましょう！

