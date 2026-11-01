"""MotionWatch v5.2 – Generator für die neuen Kleinteile (parametrisch, Masse oben in v52.py):
  12_Blindstopfen_Weitwinkel  einrastender Stopfen für das Weitwinkel-Fenster (ohne Kamera)
  13_Stopfen_IR_LED           einrastender Stopfen für das Loch der breiten IR-LED
  14_Diffusor_Status_LED      Diffusor «Blinki-Auge» für die RGB-LED auf dem Kopf (PETG natur/weiss)
  15_Pupillenring             dunkler Ring, wird oben in den Diffusor gedrückt (PETG schwarz)
Alle schon in Druckrichtung gedreht, ohne Stützen. Wichtige Parameter in v52.py:
  BLIND_TOL (Spiel 0,2 mm), BLIND_NOSE (Rastnase 0,5 mm), IR_PLUG_D, SLED_SOCK_D, DIFF_D, DIFF_H.
Aufruf:  python3 kleinteile52.py            -> out52/12..15_*.stl
         python3 kleinteile52.py 12 13      -> nur die Stopfen"""
import sys, runpy
sys.argv = [sys.argv[0]] + (sys.argv[1:] or ["12", "13", "14", "15"])
runpy.run_path("export52.py", run_name="__main__")
