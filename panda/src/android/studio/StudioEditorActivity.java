/**
 * Panda3D Studio — the in-app Python game editor.
 *
 * A simple code editor: open a .py file, edit it, Save, and Run it as a
 * 3D game.  Files live in the app's private directory.
 */

package org.panda3d.studio;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;

public class StudioEditorActivity extends Activity
        implements View.OnClickListener {

    public static final String EXTRA_PATH = "path";

    public static final String NEW_GAME_TEMPLATE =
        "# My 3D game — edit me!\n" +
        "#\n" +
        "# Hold the screen to interact with your game.\n" +
        "\n" +
        "from direct.showbase.ShowBase import ShowBase\n" +
        "from direct.gui.OnscreenText import OnscreenText\n" +
        "from panda3d.core import LColor\n" +
        "\n" +
        "class MyGame(ShowBase):\n" +
        "    def __init__(self):\n" +
        "        ShowBase.__init__(self)\n" +
        "        self.setBackgroundColor(LColor(0.2, 0.4, 0.6, 1.0))\n" +
        "\n" +
        "        # Put your game code here!\n" +
        "        # Example: load a model that ships with the app:\n" +
        "        #     model = self.loader.loadModel(\"models/panda.egg\")\n" +
        "        #     model.reparentTo(self.render)\n" +
        "        #     model.setScale(0.5)\n" +
        "\n" +
        "app = MyGame()\n" +
        "app.run()\n";

    private String path;
    private EditText code;
    private boolean dirty;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        path = getIntent().getStringExtra(EXTRA_PATH);
        if (path == null) {
            finish();
            return;
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(18, 27, 51));

        // Top bar: file name + Save / Run buttons.
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setPadding(8, 8, 8, 8);
        bar.setBackgroundColor(Color.rgb(26, 38, 68));

        TextView nameLabel = new TextView(this);
        nameLabel.setText(new File(path).getName());
        nameLabel.setTextColor(Color.WHITE);
        nameLabel.setTextSize(16);
        nameLabel.setTypeface(Typeface.MONOSPACE);
        nameLabel.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams nameLp = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        bar.addView(nameLabel, nameLp);

        bar.addView(makeButton("Save", "save"));
        bar.addView(makeButton("Run", "run"));

        code = new EditText(this);
        code.setBackgroundColor(Color.rgb(14, 20, 38));
        code.setTextColor(Color.rgb(230, 238, 250));
        code.setHint("# Write your game code here...");
        code.setHintTextColor(Color.rgb(90, 105, 140));
        code.setPadding(12, 12, 12, 12);
        code.setTextSize(14);
        code.setTypeface(Typeface.MONOSPACE);
        code.setGravity(Gravity.TOP | Gravity.START);
        code.setInputType(InputType.TYPE_CLASS_TEXT
                | InputType.TYPE_TEXT_FLAG_MULTI_LINE
                | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        code.setHorizontallyScrolling(false);
        code.setText(readFile(path));
        if (code.length() == 0) {
            code.setText(NEW_GAME_TEMPLATE);
            dirty = true;
        }

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.addView(code, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT));

        root.addView(bar);
        root.addView(scroll, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(root);
    }

    private Button makeButton(String label, String action) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(15);
        b.setPadding(20, 8, 20, 8);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.setMargins(4, 0, 4, 0);
        b.setLayoutParams(lp);
        b.setTag(action);
        b.setOnClickListener(this);
        return b;
    }

    @Override
    public void onClick(View v) {
        String action = (String) v.getTag();
        if ("save".equals(action)) {
            save();
        } else if ("run".equals(action)) {
            if (save()) {
                run();
            }
        }
    }

    private String readFile(String path) {
        try {
            InputStream in = new FileInputStream(path);
            try {
                java.io.ByteArrayOutputStream buf =
                        new java.io.ByteArrayOutputStream();
                byte[] chunk = new byte[8192];
                int n;
                while ((n = in.read(chunk)) > 0) {
                    buf.write(chunk, 0, n);
                }
                return new String(buf.toByteArray(), "UTF-8");
            } finally {
                in.close();
            }
        } catch (Exception e) {
            return "";
        }
    }

    /** Returns true on success. */
    private boolean save() {
        try {
            Writer w = new OutputStreamWriter(
                    new FileOutputStream(path), "UTF-8");
            try {
                w.write(code.getText().toString());
            } finally {
                w.close();
            }
            dirty = false;
            Toast.makeText(this, "Saved", Toast.LENGTH_SHORT).show();
            return true;
        } catch (Exception e) {
            Toast.makeText(this, "Save failed: " + e, Toast.LENGTH_LONG).show();
            return false;
        }
    }

    private void run() {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW,
                                  Uri.fromFile(new File(path)));
            i.setClassName(getPackageName(),
                           "org.panda3d.android.PythonActivity");
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Cannot start: " + e, Toast.LENGTH_LONG).show();
        }
    }

    /** Save on the way out so nothing is lost. */
    @Override
    protected void onPause() {
        super.onPause();
        if (dirty) {
            save();
        }
    }
}
