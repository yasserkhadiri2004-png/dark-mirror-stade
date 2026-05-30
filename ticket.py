import json
import cv2
from pyzbar import pyzbar

# Charger la base de tickets
with open('data/tickets.json', 'r', encoding='utf-8') as f:
    BASE_TICKETS = json.load(f)

def valider_ticket(code):
    return BASE_TICKETS.get(code.strip().upper(), None)

def saisie_manuelle():
    code = input("Entrez votre numero de ticket : ").strip().upper()
    return valider_ticket(code)

def scanner_qr():
    cap = cv2.VideoCapture(0)
    print("Presentez votre QR code - Appuyez sur Q pour annuler")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        codes = pyzbar.decode(frame)

        for code in codes:
            donnee = code.data.decode('utf-8')
            print(f"QR lu : {donnee}")
            cap.release()
            cv2.destroyAllWindows()
            return valider_ticket(donnee)

        cv2.putText(frame, "Presentez votre ticket QR",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 255), 2)
        cv2.imshow("Scanner QR", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def lire_ticket():
    """QR en premier, saisie manuelle si annulé"""
    print("\n1 - Scanner QR code")
    print("2 - Saisie manuelle")
    choix = input("Votre choix (1/2) : ").strip()

    if choix == "1":
        resultat = scanner_qr()
        if resultat:
            return resultat
        print("QR non lu - passage en saisie manuelle")
        return saisie_manuelle()
    else:
        return saisie_manuelle()

if __name__ == '__main__':
    ticket = lire_ticket()
    if ticket:
        print(f"\nTicket valide !")
        for cle, val in ticket.items():
            print(f"  {cle:12} : {val}")
    else:
        print("Ticket non reconnu.")

