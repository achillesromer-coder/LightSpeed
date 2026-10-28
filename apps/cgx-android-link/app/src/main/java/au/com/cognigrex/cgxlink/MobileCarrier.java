package au.com.cognigrex.cgxlink;

import org.json.JSONArray;
import org.json.JSONObject;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Recognition only. Neither a carrier nor an origin grants authentication or execution. */
public final class MobileCarrier {
    public static final int MAX_BYTES = 65536;
    public static final String ROOT = "cgx://cgx.cgx";
    private MobileCarrier() {}

    public static void validate(byte[] bytes) throws Exception {
        if (bytes.length > MAX_BYTES) throw new IllegalArgumentException("CGX file exceeds 64 KiB");
        String text = StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(bytes)).toString();
        JSONObject c = new JSONObject(text);
        require(c, "schema", "cgx.ls-go.mobile-link/1");
        require(c, "semantic_root", ROOT);
        require(c, "kind", "CGX-MOBILE-BOOTSTRAP/0.1");
        require(c, "binding", "CGX-MOBILE-NODE-BINDING/0.1");
        require(c, "host_node", "bouwerbase");
        require(c, "mobile_role", "roaming_operator");
        JSONArray chain = c.optJSONArray("protocol_chain");
        String[] expected = {"CGX-MOBILE-BOOTSTRAP/0.1", "CGX-DEVICE-HANDSHAKE/0.1", "CGX-NODE-EXCHANGE-CONTRACT/0.1"};
        if (chain == null || chain.length() != expected.length) throw new IllegalArgumentException("Protocol chain rejected");
        for (int i = 0; i < expected.length; i++) {
            if (!expected[i].equals(chain.opt(i))) throw new IllegalArgumentException("Protocol chain rejected");
        }
        JSONObject bridge = c.optJSONObject("bridge");
        if (bridge == null) throw new IllegalArgumentException("Bridge contract missing");
        boolean privateProfile = "owner_selected_private_https_relay".equals(bridge.opt("remote_transport"))
            && "configured_origin_only".equals(bridge.opt("discovery"))
            && "POST /api/v1/auth/login".equals(bridge.opt("owner_sign_in"));
        boolean siteProfile = "existing_owner_private_ls_go_site".equals(bridge.opt("remote_transport"))
            && "existing_site_same_origin".equals(bridge.opt("discovery"))
            && "existing_site_owner_auth".equals(bridge.opt("owner_sign_in"));
        if (!privateProfile && !siteProfile) throw new IllegalArgumentException("Bridge profile rejected");
        require(bridge, "probe", "GET /api/v1/status");
        JSONObject flags = c.optJSONObject("constraints");
        if (flags == null) throw new IllegalArgumentException("Constraints missing");
        String[] denied = {"embedded_credentials", "public_direct_execution", "automatic_owner_approval",
            "new_backend", "new_mobile_runtime", "authority_by_device", "transfer_full_corpus_on_open", "drive_write_grants_execution"};
        for (String key : denied) {
            if (!Boolean.FALSE.equals(flags.opt(key))) throw new IllegalArgumentException("Constraint rejected: " + key);
        }
        if (!Boolean.TRUE.equals(flags.opt("fail_closed_on_missing_relay_or_auth"))) {
            throw new IllegalArgumentException("Missing fail-closed policy");
        }
        // No endpoint, credential, request or authority is returned from the untrusted carrier.
    }

    private static void require(JSONObject object, String key, String expected) {
        if (!expected.equals(object.opt(key))) throw new IllegalArgumentException("Missing expected field: " + key);
    }

    public static String validateOrigin(String input) throws Exception {
        URI uri = new URI(input.trim());
        String host = uri.getHost();
        if (!"https".equals(uri.getScheme()) || host == null || host.isEmpty()
            || uri.getRawUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null
            || !(uri.getRawPath().isEmpty() || "/".equals(uri.getRawPath()))
            || uri.getPort() == 0 || uri.getPort() > 65535) {
            throw new IllegalArgumentException("Enter a plain HTTPS origin without credentials, path or query.");
        }
        host = host.toLowerCase(Locale.ROOT);
        if (host.endsWith(".")) host = host.substring(0, host.length()-1);
        if ("localhost".equals(host) || host.endsWith(".localhost") || host.startsWith("127.")
            || "0.0.0.0".equals(host) || "::1".equals(host) || "[::1]".equals(host)
            || host.contains("::ffff:127.")) {
            throw new IllegalArgumentException("A phone needs the approved private host route, not loopback.");
        }
        String value = uri.toASCIIString();
        return value.endsWith("/") ? value.substring(0, value.length()-1) : value;
    }
}
