# **Penerapan Algoritma Machine Learning Berbasis Constraint Optimization Menggunakan CP-SAT G** 

**Penerapan Algoritma Machine Learning Berbasis Constraint Optimization Menggunakan CP-SAT Google OR-Tools untuk Penjadwalan Mata Kuliah Otomatis yang Meminimalkan Bentrok Jadwal pada Mahasiswa dengan Pilihan Mata Kuliah yang Sama di Program Studi X** 

_Draf proposal awal disusun via Topic Finder Wizard JurnalHub pada 26 Oktober 2026._ 

**Pendekatan:** Kuantitatif - pengembangan sistem dan eksperimen komputasi, evaluasi kinerja algoritma dengan metrik jumlah bentrok jadwal 

**Alasan judul:** Judul ini secara langsung menguji penerapan hybrid ML berbasis constraint optimization (CP-SAT) dengan data pilihan mata kuliah mahasiswa pada satu program studi, mengisi gap kombinasi konsep yang belum pernah diteliti bersama. 

## **1. Latar Belakang & Fenomena Masalah** 

Penyusunan mata kuliah pada program studi saya dilakukan secara manual sehingga menimbulkan jadwal mata kuliah bentrok padahal kelas yang dipilih sama. 

## **2. Rumusan Masalah** 

**Bagaimana penerapan algoritma machine learning berbasis constraint optimization untuk menghasilkan penjadwalan mata kuliah otomatis yang meminimalkan bentrok jadwal pada kelas dengan pilihan mata kuliah yang sama di Program Studi X?** 

## **3. Tinjauan Literatur & Research Gap** 

Penjadwalan mata kuliah otomatis telah banyak diteliti dengan pendekatan constraint satisfaction problem (CSP), termasuk penerapan hard constraints untuk mencegah konflik dosen, ruang, dan mahasiswa [1][2][7][8], serta integrasi CSP dengan solver modern seperti CP-SAT/OR-Tools [6] dan hybrid CP dengan adaptive local search [15]. Pendekatan optimisasi lain juga mapan: mixed-integer programming dengan constraint penugasan dosen [4], genetic algorithm [5][8], hybrid GA-neural network [9], dan survey meta-heuristik untuk 

1 

UCTP [11]. Machine learning untuk academic scheduling telah di-review secara umum, mencakup supervised, unsupervised, reinforcement learning, dan hybrid [13], sementara review teknis dari integer programming menuju ML juga telah dilakukan [3]. Aspek pemilihan/sectioning mahasiswa mulai disentuh pada benchmark ITC 2019 yang menggabungkan student sectioning dengan penugasan waktu dan ruang [10], dan model preregistration UCTP dengan constraint terkait dosen [4]. Namun, tidak ada paper dalam kumpulan ini yang secara spesifik meneliti penjadwalan berbasis pilihan mata kuliah mahasiswa pada satu program studi tertentu dengan fokus meminimalkan bentrok antar mahasiswa yang memilih mata kuliah sama. 

### **_Poin Kesenjangan Penelitian (Research Gap):_** 

- Dari 15 studi yang dianalisis, belum ada yang meneliti Penjadwalan mata kuliah otomatis, Constraint optimization/CSP, Machine learning, Minimisasi bentrok jadwal, Pilihan mata kuliah mahasiswa, dan Konteks program studi secara bersamaan. 

- Paling mendekati: Gu dkk. (2025) [3] (4 dari 6 konsep), belum mencakup Pilihan mata kuliah mahasiswa dan Konteks program studi. 

- Konteks program studi belum diteliti oleh satu pun studi dalam daftar. 

- Kombinasi Machine learning dan Pilihan mata kuliah mahasiswa belum pernah diteliti bersama. 

- Kombinasi Minimisasi bentrok jadwal dan Pilihan mata kuliah mahasiswa belum pernah diteliti bersama. 

- Belum ada studi yang secara spesifik menguji algoritma machine learning berbasis constraint optimization untuk penjadwalan pada level program studi dengan input pilihan mata kuliah mahasiswa; paper ML yang ada bersifat review umum [13][3] atau hybrid GA-NN tanpa konteks pilihan mata kuliah [9]. 

- Penanganan bentrok akibat mahasiswa dengan pilihan mata kuliah yang sama belum menjadi fokus; kebanyakan paper menangani konflik dosen-ruang-kelas [1][2][7][8] [14], dan hanya [10] yang menyentuh student sectioning namun dalam konteks kompetisi benchmark, bukan prodi spesifik. 

- Tidak ada paper yang melaporkan penerapan pada satu program studi tertentu (Program Studi X) dengan data pilihan mata kuliah mahasiswa; data uji yang digunakan bersifat institusional umum atau benchmark [1][4][10]. 

2 

- Kombinasi spesifik ML dengan constraint optimization (bukan sekadar GA atau CSP murni) untuk meminimalkan bentrok jadwal belum didokumentasikan; hybrid yang ada menggabungkan CSP-GA [2][8], CP-ALS [15], atau GA-NN [9], bukan ML berbasis constraint optimization sesuai rumusan masalah. 

- Abstrak yang diberikan tidak memuat informasi tentang evaluasi tingkat bentrok pada kelas dengan pilihan mata kuliah sama sebagai metrik keberhasilan, sehingga gap ini tidak dapat dipastikan terisi oleh paper manapun. 

### **_Posisi Penelitian_** 

|**Penelitian**|**Penjadwal**<br>**an mata**<br>**kuliah**<br>**otomatis**|**Constrain**<br>**t**<br>**optimizati**<br>**on/CSP**|**Machine**<br>**learning**|**Minimisas**<br>**i bentrok**<br>**jadwal**|**Pilihan**<br>**mata**<br>**kuliah**<br>**mahasisw**<br>**a**|**Konteks**<br>**program**<br>**studi**|
|---|---|---|---|---|---|---|
|Joshi &<br>Agarwal<br>(2023) [1]|x|x|–|x|–|–|
|Ms.S.Suga<br>rthi dkk.<br>(2026) [2]|x|x|–|x|–|–|
|Gu dkk.<br>(2025) [3]|x|x|x|x|–|–|
|Algethami<br>&<br>Laesankla<br>ng (2021)<br>[4]|x|x|–|?|x|–|
|N dkk.<br>(2025) [5]|x|–|–|?|–|–|
|Kumar<br>dkk.|?|?|–|x|–|–|



3 

|**Penelitian**|**Penjadwal**<br>**an mata**<br>**kuliah**<br>**otomatis**|**Constrain**<br>**t**<br>**optimizati**<br>**on/CSP**|**Machine**<br>**learning**|**Minimisas**<br>**i bentrok**<br>**jadwal**|**Pilihan**<br>**mata**<br>**kuliah**<br>**mahasisw**<br>**a**|**Konteks**<br>**program**<br>**studi**|
|---|---|---|---|---|---|---|
|(2026) [6]|||||||
|Stephano<br>dkk.<br>(2026) [7]|x|x|–|x|–|–|
|Manuel &<br>Mohan<br>(2025) [8]|x|x|–|x|–|–|
|Hamza<br>dkk.<br>(2026) [9]|x|–|x|?|–|–|
|Müller<br>dkk.<br>(2024)<br>[10]|x|?|–|?|x|–|
|Abdipoor<br>dkk.<br>(2023)<br>[11]|x|?|–|?|–|–|
|Spracklen<br>dkk.<br>(2023)<br>[12]|–|x|–|–|–|–|
|Zanevych<br>&<br>Kukharsky<br>y (2024)|x|–|?|?|–|–|



4 

|**Penelitian**|**Penjadwal**<br>**an mata**<br>**kuliah**<br>**otomatis**|**Constrain**<br>**t**<br>**optimizati**<br>**on/CSP**|**Machine**<br>**learning**|**Minimisas**<br>**i bentrok**<br>**jadwal**|**Pilihan**<br>**mata**<br>**kuliah**<br>**mahasisw**<br>**a**|**Konteks**<br>**program**<br>**studi**|
|---|---|---|---|---|---|---|
|[13]|||||||
|Renuka<br>dkk.<br>(2026)<br>[14]|x|x|–|x|–|–|
|Zanevych<br>&<br>Kukharsky<br>y (2025)<br>[15]|?|?|–|x|–|–|
|**Penelitian**<br>**ini**|**x**|**x**|**x**|**x**|**x**|**x**|



_x = diteliti (didukung kutipan abstrak); ? = belum pasti; – = tidak diteliti._ 

## **4. Pertanyaan Penelitian (Research Questions)** 

Bagaimana penerapan algoritma machine learning berbasis constraint optimization (misalnya hybrid model pembelajaran dengan CP-SAT/OR-Tools) dapat menghasilkan jadwal mata kuliah otomatis yang meminimalkan bentrok jadwal bagi mahasiswa dengan pilihan mata kuliah yang sama pada Program Studi X? 

## **5. Daftar Pustaka Awal** 

1. Nikhil R. Joshi, Tanya Agarwal (2023). Optimizing University Course Timetabling Using Constraint Satisfaction Models. _International Academic Journal of Science and Engineering_ . 

2. Ms.S.Sugarthi Ms.S.Sugarthi, Ms.S.Aishwarya Ms.S.Aishwarya, Ms.R.Akshitha Ms.R.Akshitha, et al. (2026). Automated Timetable Generation System Using 

5 

Constraint Satisfaction and Genetic Algorithm.. _International Journal of Scientific Development and Research_ . 

3. Xin Gu, Muralee Krish, Shaleeza Sohail, et al. (2025). From Integer Programming to Machine Learning: A Technical Review on Solving University Timetabling Problems. _Computation_ . 

4. Haneen Algethami, Wasakorn Laesanklang (2021). A Mathematical Model for Course Timetabling Problem With Faculty-Course Assignment Constraints. _IEEE Access_ . 

5. Ganesh B N, Prof Geena George, H P Muruli, et al. (2025). An Optimized Machine Learning Model for Automating Academic Scheduling. _International Research Journal on Advanced Engineering Hub (IRJAEH)_ . 

6. Ankit Kumar, Adyasha Nanda, Asst. Prof. Subhalaxmi Nayak (2026). Timetable Optimizer: Automated University Schedule Generation Using CP-SAT Constraint Solving and Large Language Model Intelligence. _International Journal of LAW Arts and Humanities_ . 

7. I. Stephano, V. Logapriya, M. Kaliappan, et al. (2026). Integrated Timetable Scheduling and Faculty Workload Management System Using Constraint Satisfaction Problem Modelling. _IARJSET_ . 

8. Bincy Manuel, Vishnu Mohan (2025). Timetable Generator Using Genetic Algorithm and Constraint Satisfaction Problem. _International Journal For Multidisciplinary Research_ . 

9. Mohammed Hamza, Aminu Aminu Muazu, Musa Ahmad zayyad, et al. (2026). a A hybrid genetic algorithm-neural network framework for adaptive university timetable scheduling. _Journal of Statistical Sciences and Computational Intelligence_ . 

10. Tomáš Müller, Hana Rudová, Zuzana Müllerová (2024). Real-world university course timetabling at the International Timetabling Competition 2019. _Journal of Scheduling_ . 

11. Sina Abdipoor, Razali Yaakob, Say Leng Goh, et al. (2023). Meta-heuristic approaches for the University Course Timetabling Problem. _Intelligent Systems with Applications_ . 

12. Patrick Spracklen, Nguyen Dang, Özgür Akgün, et al. (2023). Automated streamliner portfolios for constraint satisfaction problems. _Artificial Intelligence_ . 

6 

13. Oleh Zanevych, Vitaliy Kukharskyy (2024). OVERVIEW OF MACHINE LEARNING METHODS FOR ACADEMIC SCHEDULING. _Electronics and Information Technologies_ . 

14. D. Renuka, Dr. B. Madhava Rao, R. Ajay, et al. (2026). Smart Classroom and Timetable Scheduler. _International Journal of Data Science and IoT Management System_ . 

15. Oleh Zanevych, Vitaliy Kukharskyy (2025). Solving University Timetabling Problems Using Constraint Prog. _Application Mathematics and Informatics_ . 

7 

