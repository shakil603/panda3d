/**
 * Panda3D Studio — the home screen.
 *
 * A single front door to everything: sample games, your own games (with an
 * in-app editor), and the 3D model viewer.
 */

package org.panda3d.studio;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class StudioMainActivity extends Activity
        implements View.OnClickListener {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(18, 27, 51));
        root.setPadding(0, 32, 0, 0);

        TextView title = new TextView(this);
        title.setText("Panda3D Studio");
        title.setTextColor(Color.WHITE);
        title.setTextSize(30);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER_HORIZONTAL);

        TextView subtitle = new TextView(this);
        subtitle.setText("Make 3D games on your phone");
        subtitle.setTextColor(Color.rgb(140, 160, 200));
        subtitle.setTextSize(15);
        subtitle.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitle.setPadding(0, 4, 0, 40);

        root.addView(title);
        root.addView(subtitle);

        addButton(root, "Sample Games", "Try the built-in 3D games", "samples");
        addButton(root, "My Games", "Write and run your own games", "mine");
        addButton(root, "3D Models", "View the bundled 3D models", "models");

        TextView about = new TextView(this);
        about.setText("Panda3D engine  •  games are written in Python\n"
                     + "Tap a game to run it.  Tap a model to view it.");
        about.setTextColor(Color.rgb(110, 130, 170));
        about.setTextSize(13);
        about.setGravity(Gravity.CENTER_HORIZONTAL);
        about.setPadding(24, 56, 24, 16);
        root.addView(about);

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(18, 27, 51));
        scroll.addView(root);
        setContentView(scroll);
    }

    /** Adds a big button with a caption underneath. */
    private void addButton(LinearLayout parent, String label, String caption,
                           String action) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(19);
        b.setPadding(24, 20, 24, 20);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.setMargins(40, 0, 40, 4);
        b.setLayoutParams(lp);
        b.setTag(action);
        b.setOnClickListener(this);
        parent.addView(b);

        TextView cap = new TextView(this);
        cap.setText(caption);
        cap.setTextColor(Color.rgb(110, 130, 170));
        cap.setTextSize(12);
        cap.setGravity(Gravity.CENTER_HORIZONTAL);
        cap.setPadding(0, 0, 0, 18);
        parent.addView(cap);
    }

    @Override
    public void onClick(View v) {
        String action = (String) v.getTag();
        Intent i = new Intent(this, StudioListActivity.class);
        i.putExtra(StudioListActivity.EXTRA_MODE, action);
        startActivity(i);
    }
}
