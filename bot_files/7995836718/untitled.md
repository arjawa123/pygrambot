Tambahkan total attemps 


Coin untuk beli banner profile
Dan profile avatar
Atau key untuk unlock level yang terkunci


UI adjust:
Bottom nav: samakan lebar indicator menu yang aktif
Beri jarak bottomnav dengan konten di atas nya

Hapus garis roadmap di hari terakhir, pakai titik hijau nya saja

Buatkan tombol logout di sidenav

Add dark theme toggle di pengaturan 

Kamus bisa cari vocabullary di mode kanji
Dan bisa cari bunpou di mode bunpou
Tampilkan statistik bab dan hari, bab untuk irodori dan hari intuk soumatome 



database:

add new schema entry for soumatome bunpou:
bunpou,
contoh kalimat,
terjemahan nya,
bunpou notes,
halaman pdf,
frasa kalimat,
arti frasa,
exercise
yang saya sebutkan hanya contoh, sesuaikan saja dengan best practice dan penamaan nya juga

sample data irodori sudah ada di database sekarang buat course nya dan sesuaikan juga perhitungan penilaian dan tampilan menu belajar nya
vocab_irodori:
id,bab,subchapter,kanji,yomikata,meaning,optional,pos,jp_pos,related_grammar,lesson_num
1,Bab 1,1. こんにちは,おはようございます,おはようございます,Selamat pagi.,false,["expression"],感動詞,[],1

grammar_irodori
id,level,lesson,grammar_id,pattern,meaning_id,usage,example,notes,used_vocab
1,A1,3,A1-L3-01,Nです,(Adalah) N,Digunakan untuk menyebutkan nama sendiri atau mengidentifikasi benda.,[{"id": "Saya Ton.", "jp": "トンです。", "romaji": "Ton desu."}],Dalam perkenalan diri, subjek "Watashi wa" sering dilesapkan agar lebih natural.,[]