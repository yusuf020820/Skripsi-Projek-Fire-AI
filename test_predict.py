from core.predictor import FirePredictor
p = FirePredictor("model/trained_model.pkl")
tests = [
    {"kawasan":"pemukiman","obyek":"rumah","bulan":8,"jam":20},
    {"kawasan":"pertokoan","obyek":"toko","bulan":8,"jam":10},
    {"kawasan":"pabrik","obyek":"gudang","bulan":1,"jam":2},
    {"kawasan":"pasar","obyek":"pasar","bulan":5,"jam":14},
]
for t in tests:
    print(t, "->", p.predict(t))
