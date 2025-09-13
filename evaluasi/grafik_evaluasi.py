import matplotlib.pyplot as plt
import numpy as np

# Data evaluasi
metrics = ['MAE', 'MSE', 'R²']
air_dummy = [4.02, 119.43, 0.80]
air_real = [21.71, 2612.80, -0.08]
mobil_dummy = [0.37, 0.98, 0.80]
mobil_real = [1.95, 6.62, -0.04]

x = np.arange(len(metrics))  
width = 0.2  

fig, ax = plt.subplots(figsize=(10, 6))


rects1 = ax.bar(x - width*1.5, air_dummy, width, label='Air - Dummy')
rects2 = ax.bar(x - width/2, air_real, width, label='Air - Real')
rects3 = ax.bar(x + width/2, mobil_dummy, width, label='Mobil - Dummy')
rects4 = ax.bar(x + width*1.5, mobil_real, width, label='Mobil - Real')

# Label dan tampilan
ax.set_ylabel('Nilai')
ax.set_title('Gambar 5.8 Grafik Perbandingan Evaluasi Model AI (Dummy vs Real)')
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)


def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom')

for rect_group in [rects1, rects2, rects3, rects4]:
    autolabel(rect_group)

plt.tight_layout()
plt.savefig('gambar_5_8_evaluasi.png', dpi=300)

