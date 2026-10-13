package au.com.cognigrex.cgxlink;
import org.json.JSONObject;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;

public final class MobileCarrierProbe {
    private static int checks;
    interface Attempt { void run() throws Exception; }
    private static void rejects(Attempt a) throws Exception {
        boolean failed = false;
        try { a.run(); } catch (Exception expected) { failed = true; }
        if (!failed) throw new AssertionError("Unsafe fixture accepted");
        checks++;
    }
    private static byte[] bytes(JSONObject value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    public static void main(String[] args) throws Exception {
        byte[] fixture = Files.readAllBytes(Paths.get(args[0]));
        MobileCarrier.validate(fixture); checks++;
        JSONObject c = new JSONObject(new String(fixture, StandardCharsets.UTF_8));
        c.put("semantic_root", "cgx://other");
        rejects(() -> MobileCarrier.validate(bytes(c)));
        JSONObject d = new JSONObject(new String(fixture, StandardCharsets.UTF_8));
        d.getJSONObject("constraints").put("authority_by_device", true);
        rejects(() -> MobileCarrier.validate(bytes(d)));
        d.getJSONObject("constraints").put("authority_by_device", "false");
        rejects(() -> MobileCarrier.validate(bytes(d)));
        rejects(() -> MobileCarrier.validate(new byte[65537]));
        rejects(() -> MobileCarrier.validate(new byte[]{(byte)0xff}));
        JSONObject e = new JSONObject(new String(fixture, StandardCharsets.UTF_8));
        e.put("binding", "another");
        rejects(() -> MobileCarrier.validate(bytes(e)));
        e.put("binding", "CGX-MOBILE-NODE-BINDING/0.1");
        e.remove("protocol_chain");
        rejects(() -> MobileCarrier.validate(bytes(e)));
        for (String input : new String[]{"http://private.example.test", "https://localhost", "https://127.0.0.1",
            "https://[::1]", "https://u:p@private.example.test", "https://private.example.test/path",
            "https://private.example.test?token=x", "https://private.example.test#fragment", "https://private.example.test:0"}) {
            rejects(() -> MobileCarrier.validateOrigin(input));
        }
        if (!"https://private.example.test".equals(MobileCarrier.validateOrigin("https://private.example.test/"))) throw new AssertionError();
        checks++;
        System.out.println(checks + " JVM carrier/origin checks PASS; Android Activity/APK/device NOT TESTED");
    }
}
